# routes/admin/documents.py

from flask import render_template, request, g
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from models import Document, DocumentType, Organisation, OrganisationApplication
from routes.admin import admin_bp
from utils.decorators import admin_required


@admin_bp.route('/documents')
@login_required
@admin_required
def all_documents():
    """View all documents across all organisations"""
    status_filter = request.args.get('status', '')
    doc_type_filter = request.args.get('doc_type', '')
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 20

    query = g.db.query(Document).options(
        joinedload(Document.document_type),
        joinedload(Document.organisation),
        joinedload(Document.application)
    )

    # Filter by document status
    if status_filter:
        query = query.filter(Document.status == status_filter)

    # Filter by document type
    if doc_type_filter:
        query = query.filter(Document.document_type_id == int(doc_type_filter))

    # Search by organisation name or document name
    if search:
        query = query.join(Organisation).filter(
            Organisation.name.ilike(f'%{search}%') |
            Document.original_file_name.ilike(f'%{search}%')
        )

    total = query.count()
    documents = query.order_by(
        Document.uploaded_at.desc()
    ).offset((page - 1) * per_page).limit(per_page).all()

    # Get all document types for filter dropdown
    doc_types = g.db.query(DocumentType).filter(
        DocumentType.is_active == True
    ).order_by(DocumentType.name).all()

    # Stats for summary
    total_docs = g.db.query(Document).count()
    submitted_docs = g.db.query(Document).filter(Document.status == 'submitted').count()
    accepted_docs = g.db.query(Document).filter(Document.status == 'accepted').count()
    rejected_docs = g.db.query(Document).filter(Document.status == 'rejected').count()

    return render_template(
        'admin/documents/all.html',
        documents=documents,
        doc_types=doc_types,
        status_filter=status_filter,
        doc_type_filter=doc_type_filter,
        search=search,
        page=page,
        total=total,
        per_page=per_page,
        total_docs=total_docs,
        submitted_docs=submitted_docs,
        accepted_docs=accepted_docs,
        rejected_docs=rejected_docs
    )
