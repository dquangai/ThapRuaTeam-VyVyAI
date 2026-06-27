import { useMemo, useState } from "react";

import { ApiClientError, vyvyApiClient } from "./api/client";
import {
  demoCases,
  emptyFastWarning,
  errorFastWarning,
  progressForState,
  progressStages,
  type DemoCase,
  type DemoViewState,
  type FastWarning,
  type ProgressState,
} from "./data/mockInvestigation";
import type { BehavioralRedFlag, ExpertAssessment, InvestigationResponse } from "./types";

const stateLabels: Record<DemoViewState, string> = {
  empty: "Empty",
  typing: "Typing",
  loading: "Full investigating",
  completed: "Completed",
  partial: "Partial data",
  error: "Error",
};

const riskLabels: Record<string, string> = {
  low: "Thấp",
  medium: "Trung bình",
  uncertain: "Chưa chắc chắn",
  suspicious: "Đáng nghi",
  high: "Cao",
  high_risk: "Nguy cơ cao",
  critical: "Rất cao",
};

const expertLabels: Record<string, string> = {
  cyber: "Cyber",
  financial: "Financial",
  legal_risk: "Legal Risk",
  osint: "OSINT",
};

export default function App() {
  const [selectedCaseId, setSelectedCaseId] = useState("");
  const [inputText, setInputText] = useState("");
  const [viewState, setViewState] = useState<DemoViewState>("empty");
  const [fastWarningResult, setFastWarningResult] = useState<FastWarning | null>(null);
  const [investigationResult, setInvestigationResult] = useState<InvestigationResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [copyStatus, setCopyStatus] = useState("");

  const selectedCase = useMemo(
    () => demoCases.find((demoCase) => demoCase.id === selectedCaseId) ?? null,
    [selectedCaseId],
  );
  const activeCase = selectedCase ?? demoCases[0];
  const investigation = investigationResult ?? activeCase.investigation;
  const fastWarning =
    fastWarningResult ?? (viewState === "loading" ? emptyFastWarning() : warningForState(viewState, activeCase));
  const progress = progressForState(viewState);
  const isReportVisible =
    investigationResult !== null && (viewState === "completed" || viewState === "partial");
  const isLoading = viewState === "loading";
  const isError = viewState === "error";
  const characterCount = inputText.length;

  function clearResults() {
    setFastWarningResult(null);
    setInvestigationResult(null);
    setErrorMessage("");
    setCopyStatus("");
  }

  function handleExampleChange(caseId: string) {
    setSelectedCaseId(caseId);
    clearResults();
    if (!caseId) {
      setInputText("");
      setViewState("empty");
      return;
    }

    const demoCase = demoCases.find((item) => item.id === caseId);
    if (demoCase) {
      setInputText(demoCase.text);
      setViewState("typing");
    }
  }

  async function handleAnalyze() {
    clearResults();
    const text = inputText.trim();
    if (text.length < 10) {
      setErrorMessage("Nội dung cần ít nhất 10 ký tự.");
      setViewState("error");
      return;
    }
    if (text.length > 12_000) {
      setErrorMessage("Nội dung vượt quá giới hạn 12.000 ký tự.");
      setViewState("error");
      return;
    }

    setViewState("loading");
    try {
      const request = { text, locale: "vi" as const, use_web_search: true };
      const fastCheck = await vyvyApiClient.fastCheck(request);
      setFastWarningResult(fastCheck);
      await nextFrame();

      const fullInvestigation = await vyvyApiClient.investigate(request);
      setInvestigationResult(fullInvestigation);
      if (fullInvestigation.status === "completed") {
        setViewState("completed");
      } else if (fullInvestigation.status === "partial") {
        setViewState("partial");
      } else {
        setErrorMessage("Investigation failed before a usable report was produced.");
        setViewState("error");
      }
    } catch (error) {
      setErrorMessage(
        error instanceof ApiClientError
          ? error.message
          : "Không thể hoàn tất phân tích. Vui lòng thử lại.",
      );
      setViewState("error");
    }
  }

  function handleClear() {
    setSelectedCaseId("");
    setInputText("");
    setViewState("empty");
    clearResults();
  }

  async function handleCopyReport() {
    const markdown = markdownFromInvestigation(investigation);
    if (!isReportVisible || !markdown) {
      setCopyStatus("Chưa có báo cáo để sao chép.");
      return;
    }

    try {
      await navigator.clipboard.writeText(markdown);
      setCopyStatus("Đã sao chép báo cáo Markdown.");
    } catch {
      setCopyStatus("Không thể sao chép tự động trong môi trường hiện tại.");
    }
  }

  return (
    <main className="app-shell">
      <Header />

      <section className="workspace" aria-label="VYVY demo workspace">
        <InputPanel
          characterCount={characterCount}
          inputText={inputText}
          selectedCaseId={selectedCaseId}
          viewState={viewState}
          onAnalyze={() => {
            void handleAnalyze();
          }}
          onClear={handleClear}
          onExampleChange={handleExampleChange}
          onInputChange={(value) => {
            setInputText(value);
            setViewState(value.trim() ? "typing" : "empty");
            clearResults();
          }}
        />

        <aside className="side-stack" aria-label="Fast warning and progress">
          <FastWarningCard fastWarning={fastWarning} state={viewState} />
          <ProgressCard progress={progress} state={viewState} />
        </aside>
      </section>

      <section className="report-grid" aria-label="Investigation report preview">
        <ConclusionCard
          investigation={investigation}
          isError={isError}
          isLoading={isLoading}
          isReportVisible={isReportVisible}
          errorMessage={errorMessage}
          state={viewState}
        />
        <ExpertConsensusCard investigation={investigation} visible={isReportVisible} />
        <EvidenceCard investigation={investigation} visible={isReportVisible} />
        <BehavioralCard investigation={investigation} visible={isReportVisible} />
        <RecommendationsCard
          copyStatus={copyStatus}
          investigation={investigation}
          visible={isReportVisible}
          onCopyReport={() => {
            void handleCopyReport();
          }}
        />
        <LimitationsCard investigation={investigation} state={viewState} visible={isReportVisible} />
      </section>
    </main>
  );
}

function Header() {
  return (
    <header className="hero" aria-labelledby="page-title">
      <div className="brand-mark" aria-hidden="true">
        VY
      </div>
      <div>
        <div className="hero-badges">
          <span className="badge">Hackathon MVP — Text Only</span>
          <span className="badge badge-blue">Mock Mode</span>
        </div>
        <p className="eyebrow">Investigate. Debate. Verify. Explain.</p>
        <h1 id="page-title">VYVY</h1>
        <p className="subtitle">
          AI Investigation &amp; Verification Engine cho nội dung văn bản đáng nghi.
        </p>
      </div>
    </header>
  );
}

interface InputPanelProps {
  characterCount: number;
  inputText: string;
  selectedCaseId: string;
  viewState: DemoViewState;
  onAnalyze: () => void;
  onClear: () => void;
  onExampleChange: (caseId: string) => void;
  onInputChange: (value: string) => void;
}

function InputPanel({
  characterCount,
  inputText,
  selectedCaseId,
  viewState,
  onAnalyze,
  onClear,
  onExampleChange,
  onInputChange,
}: InputPanelProps) {
  const selectedDemoCase = demoCases.find((demoCase) => demoCase.id === selectedCaseId);

  return (
    <section className="panel input-panel" aria-labelledby="input-heading">
      <div className="section-heading">
        <div>
          <p className="section-kicker">Text input</p>
          <h2 id="input-heading">Dán nội dung cần kiểm tra</h2>
        </div>
        <span className="state-pill">{stateLabels[viewState]}</span>
      </div>

      <label className="field-label" htmlFor="message-input">
        Nội dung văn bản
      </label>
      <textarea
        id="message-input"
        aria-describedby="privacy-note character-counter"
        maxLength={12_000}
        placeholder="Ví dụ: Tài khoản của bạn sẽ bị khóa, vui lòng cung cấp OTP..."
        value={inputText}
        onChange={(event) => onInputChange(event.target.value)}
      />

      <div className="input-meta">
        <span id="character-counter">{characterCount.toLocaleString("vi-VN")} / 12.000 ký tự</span>
        <span id="privacy-note">Không lưu nội dung trong MVP demo.</span>
      </div>

      <div className="control-grid">
        <label className="field-label" htmlFor="example-selector">
          Chọn ví dụ demo
        </label>
        <select
          id="example-selector"
          value={selectedCaseId}
          onChange={(event) => onExampleChange(event.target.value)}
        >
          <option value="">Chọn một ví dụ...</option>
          {demoCases.map((demoCase) => (
            <option key={demoCase.id} value={demoCase.id}>
              {demoCase.label}
            </option>
          ))}
        </select>

        <p className="integration-note" role="status">
          Fast Check sẽ chạy trước, sau đó frontend tự gọi Full Investigation.
        </p>
      </div>

      {selectedCaseId ? (
        <p className="example-note">
          {selectedDemoCase?.description}
          {selectedDemoCase ? (
            <>
              <br />
              Expected demo band: Fast {riskLabels[selectedDemoCase.expectedRiskBand.fast]} / Full{" "}
              {riskLabels[selectedDemoCase.expectedRiskBand.full]}
            </>
          ) : null}
        </p>
      ) : null}

      <div className="button-row">
        <button className="primary-button" type="button" onClick={onAnalyze}>
          Phân tích văn bản
        </button>
        <button className="secondary-button" type="button" onClick={onClear}>
          Đặt lại nội dung
        </button>
      </div>
    </section>
  );
}

function FastWarningCard({
  fastWarning,
  state,
}: {
  fastWarning: FastWarning;
  state: DemoViewState;
}) {
  const topFlags = fastWarning.triggered_flags.slice(0, 3);
  const isWaitingForFastCheck = state === "loading" && fastWarning.request_id === "empty";

  return (
    <section className="panel" aria-labelledby="fast-warning-heading">
      <div className="section-heading">
        <div>
          <p className="section-kicker">Fast Warning</p>
          <h2 id="fast-warning-heading">Cảnh báo nhanh</h2>
        </div>
        <RiskBadge label={fastWarning.risk_band} score={fastWarning.score} />
      </div>

      <p className="card-summary">
        {isWaitingForFastCheck ? "Đang chạy Fast Check..." : fastWarning.message}
      </p>
      <ul className="flag-list" aria-label="Top red flags">
        {topFlags.length > 0 ? (
          topFlags.map((flag) => (
            <li key={flag.code}>
              <strong>{flag.label}</strong>
              <span>“{flag.evidence_span}”</span>
            </li>
          ))
        ) : (
          <li>Chưa có red flag trong trạng thái hiện tại.</li>
        )}
      </ul>
      <div className="action-callout">
        <span aria-hidden="true">→</span>
        <p>{fastWarning.immediate_actions[0]}</p>
      </div>
      <p className="muted">
        {isWaitingForFastCheck
          ? "Frontend đang gọi /api/v1/fast-check."
          : state === "loading"
          ? "Đang tiếp tục điều tra đa nguồn bằng dữ liệu mock..."
          : `Latency demo: ${fastWarning.latency_ms}ms`}
      </p>
    </section>
  );
}

function ProgressCard({
  progress,
  state,
}: {
  progress: ProgressState[];
  state: DemoViewState;
}) {
  return (
    <section className="panel" aria-labelledby="progress-heading">
      <div className="section-heading">
        <div>
          <p className="section-kicker">Progress stages</p>
          <h2 id="progress-heading">Tiến trình điều tra</h2>
        </div>
      </div>
      <ol className="progress-list">
        {progressStages.map((stage, index) => (
          <li className={`progress-item ${progress[index]}`} key={stage}>
            <span className="progress-dot" aria-hidden="true" />
            <span>{stage}</span>
            <em>{progressLabel(progress[index])}</em>
          </li>
        ))}
      </ol>
      <p className="muted">
        {state === "partial"
          ? "Một số dữ liệu chưa đầy đủ; giao diện vẫn hiển thị phần có sẵn."
          : state === "loading"
          ? "Đang gọi backend theo thứ tự Fast Check rồi Full Investigation."
          : "Tiến trình phản ánh trạng thái trả về từ backend hoặc trạng thái chờ."}
      </p>
    </section>
  );
}

function ConclusionCard({
  errorMessage,
  investigation,
  isError,
  isLoading,
  isReportVisible,
  state,
}: {
  errorMessage: string;
  investigation: InvestigationResponse;
  isError: boolean;
  isLoading: boolean;
  isReportVisible: boolean;
  state: DemoViewState;
}) {
  if (isError) {
    return (
      <section className="panel report-card span-2" aria-labelledby="conclusion-heading">
        <p className="section-kicker">Conclusion</p>
        <h2 id="conclusion-heading">Không thể hiển thị kết quả</h2>
        <p className="card-summary">
          {errorMessage || "Không thể hoàn tất phân tích. Không có raw exception được hiển thị."}
        </p>
      </section>
    );
  }

  if (isLoading) {
    return (
      <section className="panel report-card span-2 loading-panel" aria-labelledby="conclusion-heading">
        <p className="section-kicker">Conclusion</p>
        <h2 id="conclusion-heading">Đang tạo báo cáo...</h2>
        <p className="skeleton-line" />
        <p className="skeleton-line short" />
      </section>
    );
  }

  if (!isReportVisible) {
    return (
      <section className="panel report-card span-2" aria-labelledby="conclusion-heading">
        <p className="section-kicker">Conclusion</p>
        <h2 id="conclusion-heading">Chưa có báo cáo</h2>
        <p className="card-summary">
          {state === "typing"
            ? "Nội dung đã sẵn sàng. Nhấn “Phân tích văn bản” để chạy Fast Warning và báo cáo."
            : "Chọn ví dụ hoặc nhập văn bản để bắt đầu demo text-only."}
        </p>
      </section>
    );
  }

  return (
    <section className="panel report-card span-2" aria-labelledby="conclusion-heading">
      <div className="score-layout">
        <div>
          <p className="section-kicker">Conclusion</p>
          <h2 id="conclusion-heading">
            {investigation.report.conclusion ?? "Báo cáo chưa có kết luận."}
          </h2>
          <p className="card-summary">
            Confidence score: {confidenceScore(investigation)}/100 · Status:{" "}
            {investigation.status}
          </p>
        </div>
        <RiskMeter
          label={riskLabel(investigation)}
          score={riskScore(investigation)}
        />
      </div>
      <ul className="reason-list">
        {reportWhy(investigation).map((reason) => (
          <li key={reason}>{reason}</li>
        ))}
      </ul>
    </section>
  );
}

function ExpertConsensusCard({
  investigation,
  visible,
}: {
  investigation: InvestigationResponse;
  visible: boolean;
}) {
  return (
    <section className="panel report-card" aria-labelledby="expert-heading">
      <p className="section-kicker">Expert consensus</p>
      <h2 id="expert-heading">Đồng thuận chuyên gia</h2>
      {!visible ? (
        <p className="empty-copy">Chưa có đánh giá chuyên gia trong trạng thái này.</p>
      ) : (
        <>
          <p className="card-summary">
            Consensus: {expertConsensus(investigation).consensus_label} ·{" "}
            {expertConsensus(investigation).consensus_score}/100
          </p>
          <div className="expert-list">
            {expertDetails(investigation).map((expert) => (
              <details key={expert.expert}>
                <summary>
                  <span>{expertLabels[expert.expert]}</span>
                  <strong>{displayScore(expert)}/100</strong>
                </summary>
                <ul>
                  {expertReasons(expert).map((reason) => (
                    <li key={`${expert.expert}-${reason.text}`}>
                      {reason.text}
                      {reason.evidence_ids.length > 0 ? (
                        <span className="citation">Evidence: {reason.evidence_ids.join(", ")}</span>
                      ) : null}
                    </li>
                  ))}
                </ul>
              </details>
            ))}
          </div>
        </>
      )}
    </section>
  );
}

function EvidenceCard({
  investigation,
  visible,
}: {
  investigation: InvestigationResponse;
  visible: boolean;
}) {
  const evidence = investigation.evidence ?? [];

  return (
    <section className="panel report-card" aria-labelledby="evidence-heading">
      <p className="section-kicker">Evidence</p>
      <h2 id="evidence-heading">Bằng chứng</h2>
      {!visible ? (
        <p className="empty-copy">Bằng chứng sẽ xuất hiện sau khi backend trả báo cáo.</p>
      ) : evidence.length === 0 ? (
        <div className="empty-state-card">
          <strong>No evidence found</strong>
          <p>Không có bằng chứng ngoài trong trạng thái partial này.</p>
        </div>
      ) : (
        <div className="evidence-list">
          {evidence.map((item) => (
            <article className="evidence-card" key={item.evidence_id}>
              <div>
                <h3>{item.title}</h3>
                <p>{item.snippet}</p>
              </div>
              <dl>
                <div>
                  <dt>Nguồn</dt>
                  <dd>{item.source_name}</dd>
                </div>
                <div>
                  <dt>Credibility</dt>
                  <dd>{item.credibility_score}/100</dd>
                </div>
                <div>
                  <dt>Relevance</dt>
                  <dd>{item.relevance_score}/100</dd>
                </div>
              </dl>
              <a href={item.url} rel="noreferrer" target="_blank">
                Mở nguồn evidence
              </a>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function BehavioralCard({
  investigation,
  visible,
}: {
  investigation: InvestigationResponse;
  visible: boolean;
}) {
  const behavioralFlags = behavioralRedFlags(investigation);

  return (
    <section className="panel report-card" aria-labelledby="behavior-heading">
      <p className="section-kicker">Behavioral red flags</p>
      <h2 id="behavior-heading">Dấu hiệu thao túng</h2>
      {!visible ? (
        <p className="empty-copy">Chưa có phân tích hành vi.</p>
      ) : (
        <>
          <p className="card-summary">{behavioralSummary(investigation)}</p>
          <ul className="behavior-list">
            {behavioralFlags.map((flag) => (
              <li key={`${flag.type}-${flag.evidence_span}`}>
                <strong>{flag.type}</strong>
                <span className={`severity severity-${flag.severity}`}>{flag.severity}</span>
                <p>“{flag.evidence_span}” — {flag.explanation}</p>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}

function RecommendationsCard({
  copyStatus,
  investigation,
  visible,
  onCopyReport,
}: {
  copyStatus: string;
  investigation: InvestigationResponse;
  visible: boolean;
  onCopyReport: () => void;
}) {
  return (
    <section className="panel report-card" aria-labelledby="recommendation-heading">
      <p className="section-kicker">Recommendations</p>
      <h2 id="recommendation-heading">Khuyến nghị hành động</h2>
      {!visible ? (
        <p className="empty-copy">Khuyến nghị sẽ hiển thị sau khi báo cáo sẵn sàng.</p>
      ) : (
        <ul className="recommendation-list">
          {recommendedActions(investigation).map((action) => (
            <li key={action}>{action}</li>
          ))}
        </ul>
      )}
      <button className="secondary-button full-width" type="button" onClick={onCopyReport}>
        Sao chép báo cáo Markdown
      </button>
      {copyStatus ? (
        <p className="muted" role="status">
          {copyStatus}
        </p>
      ) : null}
    </section>
  );
}

function LimitationsCard({
  investigation,
  state,
  visible,
}: {
  investigation: InvestigationResponse;
  state: DemoViewState;
  visible: boolean;
}) {
  const limitations = visible
    ? reportLimitations(investigation)
    : [
        "Giao diện hiện dùng dữ liệu mock, chưa gọi API thật.",
        "Không hỗ trợ OCR, ảnh, PDF, upload file, đăng nhập hoặc cơ sở dữ liệu.",
        `Trạng thái hiện tại: ${stateLabels[state]}.`,
      ];

  return (
    <section className="panel report-card span-2" aria-labelledby="limitation-heading">
      <p className="section-kicker">Limitations</p>
      <h2 id="limitation-heading">Giới hạn</h2>
      <ul className="limitation-list">
        {limitations.map((limitation) => (
          <li key={limitation}>{limitation}</li>
        ))}
      </ul>
      {visible ? (
        <p className="muted">
          Evidence mode: {investigation.evidence_status?.mode ?? "unavailable"} · Total latency:{" "}
          {investigation.timings_ms.total ?? 0}ms
        </p>
      ) : null}
    </section>
  );
}

function RiskBadge({ label, score }: { label: string; score: number }) {
  return (
    <span className={`risk-badge risk-${label}`}>
      {riskLabels[label] ?? label} · {score}
    </span>
  );
}

function RiskMeter({ label, score }: { label: string; score: number }) {
  return (
    <div className="risk-meter" aria-label={`Risk score ${score} trên 100`}>
      <span>{score}</span>
      <small>{riskLabels[label] ?? label}</small>
    </div>
  );
}

function warningForState(state: DemoViewState, demoCase: DemoCase): FastWarning {
  if (state === "empty" || state === "typing") {
    return emptyFastWarning();
  }
  if (state === "error") {
    return errorFastWarning();
  }
  return demoCase.fastWarning;
}

function progressLabel(state: ProgressState) {
  const labels: Record<ProgressState, string> = {
    pending: "Chờ",
    active: "Đang chạy",
    done: "Xong",
    partial: "Một phần",
    error: "Lỗi",
  };
  return labels[state];
}

function riskScore(investigation: InvestigationResponse): number {
  return investigation.report.risk_score ?? investigation.verification.risk_score;
}

function riskLabel(investigation: InvestigationResponse): string {
  return investigation.report.risk_label ?? investigation.verification.risk_label;
}

function confidenceScore(investigation: InvestigationResponse): number {
  return investigation.report.confidence_score ?? investigation.verification.confidence_score;
}

function reportWhy(investigation: InvestigationResponse): string[] {
  return nonEmptyStrings(investigation.report.why, [
    "Backend chưa cung cấp danh sách lý do chi tiết.",
  ]);
}

function recommendedActions(investigation: InvestigationResponse): string[] {
  const safetyAdvice = investigation.safety_advice;
  const safetyActions =
    isRecord(safetyAdvice) && Array.isArray(safetyAdvice.actions)
      ? safetyAdvice.actions
      : undefined;
  return nonEmptyStrings(investigation.report.actions ?? safetyActions, [
    "Xác minh qua kênh chính thức trước khi hành động.",
  ]);
}

function reportLimitations(investigation: InvestigationResponse): string[] {
  return [
    ...nonEmptyStrings(investigation.report.limitations, [
      "Frontend hiển thị các trường backend cung cấp; một số phần có thể thiếu khi kết quả partial.",
    ]),
    ...investigation.warnings,
  ];
}

function markdownFromInvestigation(investigation: InvestigationResponse): string | null {
  return typeof investigation.report.markdown === "string" ? investigation.report.markdown : null;
}

function expertConsensus(investigation: InvestigationResponse) {
  const consensus = investigation.report.expert_consensus;
  if (isRecord(consensus)) {
    return {
      consensus_score: numberOrZero(consensus.consensus_score),
      consensus_label: typeof consensus.consensus_label === "string" ? consensus.consensus_label : "unknown",
    };
  }
  return {
    consensus_score: 0,
    consensus_label: "unavailable",
  };
}

function expertDetails(investigation: InvestigationResponse): ExpertAssessment[] {
  return investigation.experts ?? [];
}

function displayScore(expert: ExpertAssessment): number {
  return numberOrZero(expert.score);
}

function expertReasons(expert: ExpertAssessment) {
  if (!Array.isArray(expert.reasons)) {
    return [
      {
        text: "Không có chi tiết lý do từ backend.",
        evidence_ids: expert.cited_evidence_ids,
      },
    ];
  }
  return expert.reasons
    .filter(isRecord)
    .map((reason) => ({
      text: typeof reason.text === "string" ? reason.text : "Lý do không có nội dung.",
      evidence_ids: Array.isArray(reason.evidence_ids)
        ? reason.evidence_ids.filter((item): item is string => typeof item === "string")
        : [],
    }));
}

function behavioralRedFlags(investigation: InvestigationResponse): BehavioralRedFlag[] {
  return (
    investigation.behavioral_analysis?.red_flags ??
    investigation.report.behavioral_red_flags ??
    []
  );
}

function behavioralSummary(investigation: InvestigationResponse): string {
  return investigation.behavioral_analysis?.summary ?? "Backend chưa cung cấp tóm tắt hành vi.";
}

function nonEmptyStrings(value: unknown, fallback: string[]): string[] {
  if (!Array.isArray(value)) {
    return fallback;
  }
  const strings = value.filter((item): item is string => typeof item === "string" && item.length > 0);
  return strings.length > 0 ? strings : fallback;
}

function numberOrZero(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function nextFrame(): Promise<void> {
  return new Promise((resolve) => {
    window.requestAnimationFrame(() => resolve());
  });
}
