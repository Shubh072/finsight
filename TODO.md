# FinSight — Expense Management Module (Implementation Tracker)

## Phase A — Backend: Expense Core
- [x] Create SQLAlchemy models: Expense, ExpenseCategory (optional), Account, Receipt/OCR fields, audit + soft delete + indexes
- [x] Add expenses blueprint + routes
- [x] Implement `POST /api/expenses` with JWT auth, multipart receipt upload, full validation, soft-delete support groundwork
- [ ] Add supporting GET endpoints needed by Add Expense UI (categories, payment methods, user accounts)

- [x] Add duplicate detection API/helper (used for warning)


## Phase B — Frontend: Add Expense
- [x] Verify frontend structure (static HTML) and create Add Expense page
- [ ] Implement reusable UI components for fields/cards/selects/receipt upload/tags/markdown
- [x] Implement smart category suggestion (frontend keyword heuristic)
- [ ] Implement receipt preview + client-side receipt validation
- [x] Implement draft autosave + resume
- [ ] Implement offline queueing + replay
- [x] Add duplicate detection warning before submit
- [ ] Animated success screen + redirect


## Phase C — Quality & Testing
- [ ] Add Postman collection items
- [ ] Manual test checklist (JWT, validation errors, multipart, offline)
- [ ] Ensure responsive UI and loading/skeleton/toasts

