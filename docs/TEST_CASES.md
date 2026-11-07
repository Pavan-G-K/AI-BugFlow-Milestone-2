# AI BugFlow — Acceptance Test Cases

| ID | Area | Test | Expected result |
|---|---|---|---|
| TC-01 | Auth | Sign in with demo credentials | JWT issued and dashboard opens |
| TC-02 | Auth | Sign in with wrong password | API rejects with 401 |
| TC-03 | Issue | Create issue with valid title and classification | Issue is saved and appears in issue list |
| TC-04 | Classification | Submit unsupported severity/type/priority | API rejects invalid value |
| TC-05 | Search | Search by issue key/title/module | Matching issues are displayed |
| TC-06 | ML | Request severity prediction | Suggested severity and confidence are returned |
| TC-07 | Comments | Add a comment | Comment persists with author and timestamp |
| TC-08 | Attachments | Upload a screenshot/log | File is saved and download link appears |
| TC-09 | Activity | Create issue/comment/upload attachment | Activity history records the actions |
| TC-10 | Sprint | Create sprint with end date before start date | API rejects request |
| TC-11 | Backlog | Assign backlog issue to a sprint | Issue disappears from backlog and appears on board |
| TC-12 | Board | Move Open issue to In Progress | Board reflects new status |
| TC-13 | Workflow | Change Open directly to Closed | API rejects invalid transition |
| TC-14 | Workflow | Open → In Progress → Testing → Resolved → Closed | Each valid transition succeeds |
| TC-15 | Persistence | Restart backend and reload issue list | Saved data remains in SQLite |
| TC-16 | Regression | Create issue, comment, sprint assignment | All features remain available together |

## Manual API workflow
1. Log in using `/api/auth/login`.
2. Create an issue using `/api/issues`.
3. Add a comment using `/api/issues/{id}/comments`.
4. Create a sprint using `/api/sprints`.
5. Assign issue using `/api/issues/{id}/assign-sprint/{sprint_id}`.
6. Advance status through the allowed lifecycle.
7. Inspect `/api/issues/{id}/activity` and `/api/sprints/{sprint_id}/board`.
