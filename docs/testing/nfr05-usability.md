# NFR-05 usability test kit

NFR-05: a first-time driver reserves a slot in 1 minute or less, without instructions. Verification method: Demonstration. Plan task T-05 (Sprint 3), with 3 drivers.

The team runs the sessions and fills in the results table. This file only prepares the materials.

## Preparation

1. Reset the demo database: stop the backend, delete `backend/spms.db`, then start `npm run dev:be` and `npm run dev:fe`.
2. Open `http://localhost:5173` on the device the participant will use. Log in as `driver` / `driver123`. Stop at the Driver tab. Do not show the participant the reservation card beforehand.
3. Have a stopwatch ready (phone is fine) and a printed or on-screen copy of the task below.
4. Prefer participants who have never used SPMS. Record whether each one has.

## Task given to each participant

Read this aloud, then say nothing else except to answer "yes, you can start":

> **Đặt chỗ một slot trống ở tầng 1.** Biển số xe của bạn là `30A-123.45`. Nói "xong" khi bạn thấy chỗ đã được giữ cho bạn.

Do not explain the screen, the buttons or the plate format. If the participant asks how to do something, answer "hãy làm như bạn nghĩ là đúng" and note the question under comments.

## Start and stop points

| Point | Moment |
|---|---|
| Start | The participant says "yes, I can start" while the logged-in Driver tab is on screen. Start the stopwatch. |
| Stop | The "Your reservation" card with the slot ID and the countdown is visible. Stop the stopwatch. |
| Failure | The participant gives up, or 3 minutes pass without a visible reservation. Record "no" and the time reached. |

Between participants, cancel the reservation (button "Cancel reservation") or reset the database so the slot picker is shown again.

## Results

Pass criterion: every one of the 3 participants succeeds in 60 seconds or less. Fill in one row per participant.

| # | Participant (initials) | First time using the app (yes/no) | Time (seconds) | Success (yes/no) | Comments (hesitations, wrong clicks, questions) |
|---|---|---|---|---|---|
| 1 |  |  |  |  |  |
| 2 |  |  |  |  |  |
| 3 |  |  |  |  |  |

| Summary | Value |
|---|---|
| Date and place |  |
| Device and browser |  |
| Slowest time (seconds) |  |
| Result (pass if all succeeded in 60 s or less) |  |

After the sessions, copy the summary into the Excel sheet `nfrs` for NFR-05 and into traceability (`docs/requirements/traceability.md`, NFR-05 status). If a participant is slow, the comments column should say which step cost the time (finding the slot, typing the plate, finding the button), so the interface can be fixed.

## Consent note (read before the session)

> Chúng tôi đang kiểm tra giao diện đặt chỗ của hệ thống bãi xe SPMS cho môn học CSE703095. Chúng tôi đo thời gian bạn hoàn thành một việc, không đánh giá bạn. Bạn có thể dừng bất cứ lúc nào. Chúng tôi chỉ ghi lại chữ cái đầu tên bạn, thời gian, và nhận xét của bạn; không ghi hình, không ghi âm. Biển số `30A-123.45` là biển số mẫu, không phải dữ liệu thật của bạn. Bạn đồng ý tham gia không?

Record the verbal consent ("có") in the comments column if you do not collect a signature.
