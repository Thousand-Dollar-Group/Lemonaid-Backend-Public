## Associated Task and sub-task with brief description

**Example: [Task #935-1](https://)**

- Refactor ProcessPayment to allow for blocking/non-blocking locks (SELECT FOR SHARE, SKIP LOCKED)
- Unit tests for LockPaymentExclusive

## What and why are you proposing this implement/fix?

**Current**

Example

- No locking mechanism implemented for updating data in the database
- This causes race conditions when multiple processes concurrently manipulate a specific payment

**New**

Example

(To highlight the purpose of the change, explain how the modified files contribute to that goal, and describe how the updated code relates to other files, if applicable.)

Implement database locking with support for both waiting to acquire the lock and immediately giving up if the lock is held.

- pkg/db.go: Changed LockPaymentExclusive
  - Added block boolean argument. if true, the function tries to block when acquiring a lock, otherwise it gives up straightaway if someone else is holding the lock
  - Added locked boolean return value. If true, the lock is acquired; otherwise, either someone else holds the lock (no error) or an error occurred (lock not acquired).
- tests/pkg_tests/db_test.go
  - Added unit tests for LockPaymentExclusive in db_test.go

**Plan**

Example
(To show reviewers that you've intentionally broken down the work into smaller, manageable PRs and plan to address the remaining tasks in a follow-up PR.)

- Implement sweep function using the updated locking mechanism

## Explain your implement/fix

#### Pull request type

- [ ] Bugfix
- [x] Feature
- [ ] Code style update (formatting, renaming)
- [ ] Refactoring (no functional changes, no api changes)
- [ ] Build related changes
- [ ] Documentation content changes (README)
- [ ] Other (please describe):

## Does this close or depend on any currently open issues or pull request?

closes #<issue-number>

(When the PR is merged → GitHub automatically closes issue #123.)

depends on #<pr-number>

(the current PR should not be reviewed or merged until PR #456 is merged.)

## Any relevant logs, error output, comments etc?

## Where has this been tested?

- [x] Local (``)
- [ ] Github Actions
