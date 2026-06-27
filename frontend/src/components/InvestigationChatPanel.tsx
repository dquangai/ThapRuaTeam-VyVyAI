import {
  useEffect,
  useId,
  useRef,
  useState,
  type KeyboardEvent,
  type ReactNode,
  type RefObject,
} from "react";

import type { DemoCase, DemoViewState, FastWarning, ProgressState } from "../data/mockInvestigation";
import { progressStages } from "../data/mockInvestigation";
import type { InvestigationResponse } from "../types";

interface InvestigationChatPanelProps {
  demoCases: DemoCase[];
  errorMessage: string;
  fastWarning: FastWarning;
  hasFastWarningResult: boolean;
  inputText: string;
  investigation: InvestigationResponse;
  isLoading: boolean;
  isReportVisible: boolean;
  progress: ProgressState[];
  selectedCaseId: string;
  submittedAt: string | null;
  submittedText: string;
  viewState: DemoViewState;
  onAnalyze: () => void;
  onDemoSelect: (caseId: string) => void;
  onInputChange: (value: string) => void;
  onNewInvestigation: () => void;
  onReportFocus: () => void;
  onRetry: () => void;
}

const chatStateLabels: Record<DemoViewState, string> = {
  empty: "Sẵn sàng phân tích",
  typing: "Sẵn sàng phân tích",
  loading: "Đang điều tra đa nguồn",
  completed: "Đã hoàn thành",
  partial: "Kết quả một phần",
  error: "Không thể hoàn thành",
};

const quickReplyLabels: Record<string, string> = {
  "bank-otp-phishing": "Lừa đảo OTP",
  "fake-authority-payment": "Mạo danh cơ quan",
  "recruitment-fee": "Tuyển dụng thu phí",
  "marketplace-login-link": "Link nhận tiền",
  "benign-school-reminder": "Tin nhắn an toàn",
};

const stageLabels = [
  "Hiểu nội dung",
  "Tìm kiếm bằng chứng",
  "Chuyên gia phân tích",
  "Trọng tài xác thực",
  "Tạo báo cáo",
];

const progressLabels: Record<ProgressState, string> = {
  pending: "Đang chờ",
  active: "Đang chạy",
  done: "Hoàn tất",
  partial: "Một phần",
  error: "Không khả dụng",
};

export function InvestigationChatPanel({
  demoCases,
  errorMessage,
  fastWarning,
  hasFastWarningResult,
  inputText,
  investigation,
  isLoading,
  isReportVisible,
  progress,
  selectedCaseId,
  submittedAt,
  submittedText,
  viewState,
  onAnalyze,
  onDemoSelect,
  onInputChange,
  onNewInvestigation,
  onReportFocus,
  onRetry,
}: InvestigationChatPanelProps) {
  const threadRef = useRef<HTMLDivElement | null>(null);
  const subtitle =
    viewState === "loading" && !hasFastWarningResult
      ? "Đang kiểm tra nhanh"
      : chatStateLabels[viewState];

  useEffect(() => {
    const thread = threadRef.current;
    if (!thread) {
      return;
    }
    thread.scrollTo({ top: thread.scrollHeight, behavior: "smooth" });
  }, [errorMessage, fastWarning.request_id, isReportVisible, submittedText, viewState]);

  return (
    <section className="column input-column investigation-chat-panel" aria-labelledby="chat-panel-title">
      <ChatHeader
        subtitle={subtitle}
        viewState={viewState}
        onNewInvestigation={onNewInvestigation}
      />

      <ChatThread
        errorMessage={errorMessage}
        fastWarning={fastWarning}
        hasFastWarningResult={hasFastWarningResult}
        investigation={investigation}
        isLoading={isLoading}
        isReportVisible={isReportVisible}
        progress={progress}
        submittedAt={submittedAt}
        submittedText={submittedText}
        threadRef={threadRef}
        viewState={viewState}
        onReportFocus={onReportFocus}
        onRetry={onRetry}
      />

      <div className="chat-panel-footer">
        <DemoQuickReplies
          demoCases={demoCases}
          disabled={isLoading}
          selectedCaseId={selectedCaseId}
          onDemoSelect={onDemoSelect}
        />
        <ChatComposer
          disabled={isLoading}
          value={inputText}
          onChange={onInputChange}
          onSubmit={onAnalyze}
        />
      </div>
    </section>
  );
}

function ChatHeader({
  subtitle,
  viewState,
  onNewInvestigation,
}: {
  subtitle: string;
  viewState: DemoViewState;
  onNewInvestigation: () => void;
}) {
  return (
    <header className="chat-panel-header">
      <div className="chat-assistant-title">
        <span className="chat-avatar" aria-hidden="true">
          V
        </span>
        <div>
          <h2 id="chat-panel-title">Trợ lý điều tra VYVY</h2>
          <p>{subtitle}</p>
        </div>
      </div>
      <div className="chat-header-actions">
        <span className={`chat-status-dot chat-status-${viewState}`} aria-hidden="true" />
        <button
          aria-label="Tạo cuộc điều tra mới"
          className="icon-button"
          title="Tạo cuộc điều tra mới"
          type="button"
          onClick={onNewInvestigation}
        >
          ↻
        </button>
      </div>
    </header>
  );
}

function ChatThread({
  errorMessage,
  fastWarning,
  hasFastWarningResult,
  investigation,
  isLoading,
  isReportVisible,
  progress,
  submittedAt,
  submittedText,
  threadRef,
  viewState,
  onReportFocus,
  onRetry,
}: {
  errorMessage: string;
  fastWarning: FastWarning;
  hasFastWarningResult: boolean;
  investigation: InvestigationResponse;
  isLoading: boolean;
  isReportVisible: boolean;
  progress: ProgressState[];
  submittedAt: string | null;
  submittedText: string;
  threadRef: RefObject<HTMLDivElement | null>;
  viewState: DemoViewState;
  onReportFocus: () => void;
  onRetry: () => void;
}) {
  const shouldShowProgress = Boolean(submittedText) && (isLoading || isReportVisible || viewState === "error");
  const shouldShowAck = Boolean(submittedText) && (isLoading || hasFastWarningResult || isReportVisible);

  return (
    <div className="chat-thread" ref={threadRef} aria-live="polite">
      {!submittedText ? <WelcomeMessage /> : null}

      {submittedText ? <UserMessage text={submittedText} timestamp={submittedAt} /> : null}

      {shouldShowAck ? (
        <AssistantBubble>
          <p>Đã nhận nội dung. VYVY đang thực hiện kiểm tra rủi ro ban đầu.</p>
        </AssistantBubble>
      ) : null}

      {hasFastWarningResult ? <FastWarningMessage fastWarning={fastWarning} /> : null}

      {shouldShowProgress ? <InvestigationProgressMessage progress={progress} viewState={viewState} /> : null}

      {isReportVisible ? (
        <InvestigationSummaryMessage investigation={investigation} onReportFocus={onReportFocus} />
      ) : null}

      {viewState === "partial" && isReportVisible ? <PartialResultMessage investigation={investigation} /> : null}

      {viewState === "error" ? (
        <ErrorMessage message={errorMessage} canRetry={Boolean(submittedText)} onRetry={onRetry} />
      ) : null}
    </div>
  );
}

function WelcomeMessage() {
  return (
    <AssistantBubble>
      <p>
        Xin chào, tôi là <strong>VYVY</strong>.
      </p>
      <p>
        Hãy gửi nội dung tin nhắn, email, quảng cáo hoặc lời mời đầu tư mà bạn nghi ngờ.
        Tôi sẽ kiểm tra dấu hiệu rủi ro, đối chiếu bằng chứng và đưa ra khuyến nghị an toàn.
      </p>
      <p className="chat-note">MVP hiện chỉ nhận nội dung văn bản.</p>
    </AssistantBubble>
  );
}

function UserMessage({ text, timestamp }: { text: string; timestamp: string | null }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const isLong = text.length > 420 || text.split(/\r?\n/).length > 6;

  return (
    <article className="chat-message user-message">
      <div className="user-bubble">
        <p className={`preserve-lines ${isLong && !isExpanded ? "is-collapsed" : ""}`}>{text}</p>
        {isLong ? (
          <button className="text-button" type="button" onClick={() => setIsExpanded((value) => !value)}>
            {isExpanded ? "Thu gọn" : "Xem thêm"}
          </button>
        ) : null}
      </div>
      {timestamp ? <time>{timestamp}</time> : null}
    </article>
  );
}

function AssistantBubble({ children }: { children: ReactNode }) {
  return (
    <article className="chat-message assistant-message">
      <span className="assistant-avatar" aria-hidden="true">
        V
      </span>
      <div className="assistant-bubble">{children}</div>
    </article>
  );
}

function FastWarningMessage({ fastWarning }: { fastWarning: FastWarning }) {
  const flags = fastWarning.triggered_flags.slice(0, 5);
  const actions = fastWarning.immediate_actions.slice(0, 4);

  return (
    <article className={`chat-message risk-message risk-message-${riskTone(fastWarning.score)}`}>
      <span className="risk-icon" aria-hidden="true">
        !
      </span>
      <div className="risk-bubble">
        <h3>Cảnh báo nhanh: {riskBandLabel(fastWarning.risk_band)}</h3>
        <p>{fastWarning.message}</p>
        <MessageList title="Phát hiện" items={flags.map((flag) => flag.label)} empty="Chưa có red flag rõ ràng." />
        <MessageList title="Khuyến nghị tức thời" items={actions} empty="Không có hành động khẩn cấp." />
        <p className="chat-meta">Fast Check: {formatScore(fastWarning.score)}/100 · {fastWarning.latency_ms}ms</p>
      </div>
    </article>
  );
}

function InvestigationProgressMessage({
  progress,
  viewState,
}: {
  progress: ProgressState[];
  viewState: DemoViewState;
}) {
  return (
    <article className="chat-message progress-message">
      <span className="assistant-avatar" aria-hidden="true">
        V
      </span>
      <div className="progress-bubble">
        <h3>Tiến trình điều tra</h3>
        <ol className="chat-progress-list">
          {progressStages.map((stage, index) => {
            const state = progress[index] ?? "pending";
            return (
              <li className={`chat-progress-item ${state}`} key={stage}>
                <span aria-hidden="true" />
                <div>
                  <strong>{stageLabels[index] ?? stage}</strong>
                  <em>{progressLabels[state]}</em>
                </div>
              </li>
            );
          })}
        </ol>
        {viewState === "loading" ? <p className="chat-meta">Thẻ này cập nhật tại chỗ, không tạo tin nhắn lặp.</p> : null}
      </div>
    </article>
  );
}

function InvestigationSummaryMessage({
  investigation,
  onReportFocus,
}: {
  investigation: InvestigationResponse;
  onReportFocus: () => void;
}) {
  const statusCopy =
    investigation.status === "partial"
      ? "Đã hoàn thành phân tích với dữ liệu chưa đầy đủ."
      : "Cuộc điều tra đã hoàn thành.";

  return (
    <AssistantBubble>
      <h3>{statusCopy}</h3>
      <dl className="summary-metrics">
        <div>
          <dt>Mức rủi ro</dt>
          <dd>{riskBandLabel(riskLabel(investigation))}</dd>
        </div>
        <div>
          <dt>Độ tin cậy</dt>
          <dd>{formatScore(confidenceScore(investigation))}%</dd>
        </div>
      </dl>
      <p>
        <strong>Kết luận:</strong> {investigation.report.conclusion ?? "Backend chưa cung cấp kết luận chi tiết."}
      </p>
      <button className="secondary-button compact-button" type="button" onClick={onReportFocus}>
        Xem báo cáo chi tiết
      </button>
    </AssistantBubble>
  );
}

function PartialResultMessage({ investigation }: { investigation: InvestigationResponse }) {
  const warnings = sanitizedWarnings(investigation);

  return (
    <AssistantBubble>
      <h3>Kết quả một phần</h3>
      <p>
        Một số nguồn hoặc chuyên gia không khả dụng. Mức rủi ro vẫn được tính từ các tín hiệu hiện có,
        trong khi độ tin cậy đã được điều chỉnh giảm.
      </p>
      <MessageList title="Lưu ý" items={warnings} empty="Không có cảnh báo bổ sung từ backend." />
    </AssistantBubble>
  );
}

function ErrorMessage({
  canRetry,
  message,
  onRetry,
}: {
  canRetry: boolean;
  message: string;
  onRetry: () => void;
}) {
  return (
    <article className="chat-message error-message" role="alert">
      <span className="risk-icon" aria-hidden="true">
        !
      </span>
      <div className="error-bubble">
        <h3>Không thể hiển thị kết quả</h3>
        <p>{sanitizeText(message) || "Yêu cầu thất bại. Vui lòng thử lại."}</p>
        {canRetry ? (
          <button className="secondary-button compact-button" type="button" onClick={onRetry}>
            Thử lại
          </button>
        ) : null}
      </div>
    </article>
  );
}

function MessageList({
  empty,
  items,
  title,
}: {
  empty: string;
  items: string[];
  title: string;
}) {
  return (
    <div className="message-list">
      <strong>{title}</strong>
      {items.length > 0 ? (
        <ul>
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p>{empty}</p>
      )}
    </div>
  );
}

function DemoQuickReplies({
  demoCases,
  disabled,
  selectedCaseId,
  onDemoSelect,
}: {
  demoCases: DemoCase[];
  disabled: boolean;
  selectedCaseId: string;
  onDemoSelect: (caseId: string) => void;
}) {
  return (
    <div className="quick-replies" aria-label="Ví dụ demo">
      {demoCases.map((demoCase) => (
        <button
          className={demoCase.id === selectedCaseId ? "is-selected" : ""}
          disabled={disabled}
          key={demoCase.id}
          type="button"
          onClick={() => onDemoSelect(demoCase.id)}
        >
          {quickReplyLabels[demoCase.id] ?? demoCase.label}
        </button>
      ))}
    </div>
  );
}

function ChatComposer({
  disabled,
  value,
  onChange,
  onSubmit,
}: {
  disabled: boolean;
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
}) {
  const textareaId = useId();
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const isComposingRef = useRef(false);
  const canSubmit = value.trim().length > 0 && !disabled;

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) {
      return;
    }
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 172)}px`;
  }, [value]);

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key !== "Enter" || event.shiftKey || isComposingRef.current || event.nativeEvent.isComposing) {
      return;
    }
    event.preventDefault();
    if (canSubmit) {
      onSubmit();
    }
  }

  return (
    <form
      className="chat-composer"
      onSubmit={(event) => {
        event.preventDefault();
        if (canSubmit) {
          onSubmit();
        }
      }}
    >
      <label className="sr-only" htmlFor={textareaId}>
        Nội dung cần điều tra
      </label>
      <textarea
        aria-describedby={`${textareaId}-counter ${textareaId}-hint`}
        disabled={disabled}
        id={textareaId}
        maxLength={12_000}
        placeholder="Nhập nội dung cần điều tra..."
        ref={textareaRef}
        rows={1}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onCompositionEnd={() => {
          isComposingRef.current = false;
        }}
        onCompositionStart={() => {
          isComposingRef.current = true;
        }}
        onKeyDown={handleKeyDown}
      />
      <div className="composer-footer">
        <span id={`${textareaId}-counter`}>{value.length.toLocaleString("vi-VN")} / 12.000</span>
        <span id={`${textareaId}-hint`}>Enter để gửi · Shift+Enter xuống dòng</span>
        <button
          aria-label="Phân tích nội dung"
          className="send-button"
          disabled={!canSubmit}
          title="Gửi để VYVY điều tra"
          type="submit"
        >
          {disabled ? "…" : "➤"}
        </button>
      </div>
    </form>
  );
}

function sanitizedWarnings(investigation: InvestigationResponse): string[] {
  const warnings = [
    ...(investigation.warnings ?? []),
    ...(investigation.evidence_status?.errors ?? []),
  ];
  return warnings
    .filter((warning): warning is string => typeof warning === "string" && warning.trim().length > 0)
    .map(sanitizeText)
    .slice(0, 4);
}

function confidenceScore(investigation: InvestigationResponse): number {
  return investigation.report.confidence_score ?? investigation.verification.confidence_score;
}

function riskLabel(investigation: InvestigationResponse): string {
  return investigation.report.risk_label ?? investigation.verification.risk_label;
}

function riskBandLabel(label: string): string {
  const labels: Record<string, string> = {
    critical: "Rất cao",
    high: "Cao",
    high_risk: "Nguy cơ cao",
    low: "Thấp",
    suspicious: "Đáng nghi",
    uncertain: "Chưa chắc chắn",
  };
  return labels[label] ?? label;
}

function riskTone(score: number): "high" | "medium" | "low" {
  if (score >= 70) {
    return "high";
  }
  if (score >= 35) {
    return "medium";
  }
  return "low";
}

function formatScore(value: number): string {
  if (!Number.isFinite(value)) {
    return "0";
  }
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

function sanitizeText(value: string): string {
  return value
    .replace(/sk-[A-Za-z0-9_-]+/g, "[redacted]")
    .replace(/Bearer\s+[A-Za-z0-9._~+/-]+=*/gi, "Bearer [redacted]")
    .slice(0, 240);
}
