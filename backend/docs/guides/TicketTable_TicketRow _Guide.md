# TicketTable & TicketRow — Frontend Module

## 📌 Overview

This module powers the **interactive Zendesk ticket management table** inside the OAPS ZAF app. It provides directors and staff with a seamless way to view, update, and reassign tickets in **real time** during bi-weekly meetings.

The system is made of two React components:

* **`TicketTable.jsx`** → Renders the full table, fetches OAPS users, and injects them into rows.
* **`TicketRow.jsx`** → Handles interactive logic for each ticket (status, assignee, group sync, notes, etc.).

---

## ⚙️ Features

* **Status Updates**: Change ticket status via dropdown (`open`, `pending`, `on-hold`, `solved`, `closed`).
* **Smart Reassignment**:

  * Assignee dropdown limited to **OAPS team members only**.
  * Auto-updates both **`assignee_id`** and **`group_id`** in Zendesk.
  * Group column reflects changes instantly (**optimistic UI**).
* **Age Display**: Toggle between:

  * **Buckets** (Over 30 Days, Over 20 Days, etc.)
  * **Exact Days** (e.g., `42`).
* **Closed-by-Meeting Flag**: Shows if the ticket was solved/closed during the current meeting window.
* **Notes Editor**: Inline comments, supports both internal and public notes.

---

## 🛠️ Data Flow

### 1. **TicketTable.jsx**

* Fetches OAPS users once via backend `/users` endpoint.
* Renders column headers:

  ```
  Ticket ID | Subject | Group | Status | Assignee | Age | Closed by Meeting | Notes
  ```
* Passes down:

  * `tickets`
  * `authToken`
  * `onStatus`, `onReassign`, `onNote`
  * `users` (OAPS agents)
  * `loadingUsers`

### 2. **TicketRow.jsx**

* Renders individual ticket data with interactive controls.
* **On reassignment**:

  * Finds the selected user.
  * Immediately updates **group column** (UI).
  * Calls backend to update both `assignee_id` + `group_id` in Zendesk.
* **On status change**:

  * Updates Zendesk status in real time.
* **On note submit**:

  * Adds comment (internal/public) via backend API.

---

## 🔄 Lifecycle Flow

1. `TicketTable` mounts → Fetches OAPS users list.
2. Tickets load from backend `/tickets`.
3. `TicketRow` renders each ticket with dropdowns + actions.
4. Director reassigns ticket →

   * Assignee dropdown updates.
   * Group column flips immediately.
   * Backend syncs new `assignee_id` + `group_id` with Zendesk.
5. **UI + Zendesk stay in sync** for real-time meeting review.

---

## 💻 Example Usage

```jsx
<TicketTable
  tickets={rows}
  onStatus={updateStatus}
  onReassign={reassign}
  onNote={addNote}
  showExactAge={showExactAge}
  authToken={token}
/>
```

---

## 📈 Benefits

* **Frictionless**: Directors reassign tickets in real time during meetings.
* **Consistent**: Group column always matches assignee’s Zendesk group.
* **Performant**: Fetches users once at table level (avoids N+1 API calls).
* **Scalable**: Easily extendable with filters, audit logs, or export enhancements.

---

**Author**: Olivier Lamy
**Version**: 1.0.0 | Updated: September 2025
