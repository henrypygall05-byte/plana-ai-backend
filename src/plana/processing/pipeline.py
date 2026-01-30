"""
Document processing pipeline.

Coordinates fetching, storing, and extracting text from planning documents.
"""

import asyncio
from datetime import datetime
from typing import AsyncIterator

import structlog

from plana.config import get_settings
from plana.core.models import Application, ApplicationDocument
from plana.councils.base import CouncilPortal, CouncilRegistry
from plana.processing.extractor import TextExtractor
from plana.storage.document_store import DocumentStore

logger = structlog.get_logger(__name__)


class DocumentProcessor:
    """
    Coordinates document processing pipeline.

    Handles:
    - Fetching documents from council portals
    - Storing raw documents with deduplication
    - Extracting and storing text
    - Tracking processing status
    """

    def __init__(
        self,
        document_store: DocumentStore | None = None,
        text_extractor: TextExtractor | None = None,
    ):
        """Initialize document processor.

        Args:
            document_store: Storage for documents
            text_extractor: Text extraction handler
        """
        self.document_store = document_store or DocumentStore()
        self.text_extractor = text_extractor or TextExtractor()
        self.settings = get_settings()

    async def process_application(
        self,
        application: Application,
        portal: CouncilPortal | None = None,
        force_reprocess: bool = False,
    ) -> Application:
        """Process all documents for an application.

        Args:
            application: Application to process
            portal: Council portal to use (or creates from registry)
            force_reprocess: Re-download and re-extract even if exists

        Returns:
            Updated application with processed documents
        """
        logger.info(
            "Processing application documents",
            reference=application.reference,
            council=application.council_id,
        )

        if portal is None:
            portal = CouncilRegistry.get(application.council_id)

        try:
            # Fetch document list
            documents = await portal.fetch_application_documents(application.reference)

            # Process each document
            processed_docs = []
            for doc in documents:
                try:
                    processed_doc = await self.process_document(
                        document=doc,
                        portal=portal,
                        force_reprocess=force_reprocess,
                    )
                    processed_docs.append(processed_doc)

                    # Rate limiting
                    await asyncio.sleep(self.settings.council.request_delay_seconds)

                except Exception as e:
                    logger.error(
                        "Failed to process document",
                        doc_id=doc.id,
                        error=str(e),
                    )
                    processed_docs.append(doc)  # Keep original

            application.documents = processed_docs

            logger.info(
                "Processed application documents",
                reference=application.reference,
                total=len(documents),
                processed=sum(1 for d in processed_docs if d.text_extracted),
            )

            return application

        finally:
            await portal.close()

    async def process_document(
        self,
        document: ApplicationDocument,
        portal: CouncilPortal,
        force_reprocess: bool = False,
    ) -> ApplicationDocument:
        """Process a single document.

        Args:
            document: Document to process
            portal: Portal to download from
            force_reprocess: Force re-download and re-extract

        Returns:
            Updated document with storage paths
        """
        logger.debug(
            "Processing document",
            doc_id=document.id,
            title=document.title,
        )

        # Check if already processed
        if not force_reprocess and await self.document_store.document_exists(document):
            if document.text_extracted:
                logger.debug("Document already processed", doc_id=document.id)
                return document

        # Download document
        content = await self._download_document(document, portal)
        if not content:
            return document

        # Store document
        document = await self.document_store.store_document(
            document=document,
            content=content,
            skip_if_exists=not force_reprocess,
        )

        # Extract text
        if document.is_pdf:
            result = await self.text_extractor.extract_from_pdf(content)
            if result.text:
                document = await self.document_store.store_extracted_text(
                    document=document,
                    text=result.text,
                )
                document.page_count = result.page_count
                document.metadata["extraction_method"] = result.method
                document.metadata["extraction_confidence"] = result.confidence

        elif document.file_type.lower() in ("txt", "text"):
            result = self.text_extractor.extract_from_text(content)
            if result.text:
                document = await self.document_store.store_extracted_text(
                    document=document,
                    text=result.text,
                )

        # Images need OCR which is handled separately
        elif document.is_image:
            document.metadata["needs_ocr"] = True

        return document

    async def _download_document(
        self,
        document: ApplicationDocument,
        portal: CouncilPortal,
    ) -> bytes | None:
        """Download document content.

        Args:
            document: Document to download
            portal: Portal to download from

        Returns:
            Document content as bytes or None on failure
        """
        try:
            chunks = []
            async for chunk in portal.download_document(document):
                chunks.append(chunk)
            return b"".join(chunks)
        except Exception as e:
            logger.error(
                "Failed to download document",
                doc_id=document.id,
                error=str(e),
            )
            return None

    async def get_document_text(
        self, document: ApplicationDocument
    ) -> str | None:
        """Get extracted text for a document.

        Args:
            document: Document to get text for

        Returns:
            Extracted text or None if not available
        """
        if not document.text_extracted:
            return None

        try:
            return await self.document_store.get_extracted_text(document)
        except FileNotFoundError:
            return None

    async def get_all_document_texts(
        self, application: Application
    ) -> dict[str, str]:
        """Get extracted text for all documents in an application.

        Args:
            application: Application with documents

        Returns:
            Dict mapping document IDs to text content
        """
        texts = {}
        for doc in application.documents:
            text = await self.get_document_text(doc)
            if text:
                texts[doc.id] = text
        return texts
