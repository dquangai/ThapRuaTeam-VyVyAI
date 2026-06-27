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
import type { BehavioralRedFlag, EvidenceItem, ExpertAssessment, InvestigationResponse } from "./types";

const stateLabels: Record<DemoViewState, string> = {
  empty: "Sẵn sàng",
  typing: "Đã nhập",
  loading: "Đang điều tra",
  completed: "Hoàn tất",
  partial: "Một phần",
  error: "Lỗi",
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
  cyber: "Cyber Expert",
  financial: "Financial Expert",
  legal_risk: "Legal Risk Expert",
  osint: "OSINT Expert",
};

const behavioralLabels: Record<string, string> = {
  fear: "Sợ hãi",
  urgency: "Khẩn cấp",
  isolation: "Cô lập",
  scarcity: "Khan hiếm",
  reciprocity: "Đáp trả",
  authority_pressure: "Áp lực thẩm quyền",
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
      setErrorMessage("Noi dung can it nhat 10 ky tu.");
      setViewState("error");
      return;
    }
    if (text.length > 12_000) {
      setErrorMessage("Noi dung vuot qua gioi han 12.000 ky tu.");
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
          : "Khong the hoan tat phan tich. Vui long thu lai.",
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
      setCopyStatus("Chua co bao cao de sao chep.");
      return;
    }

    try {
      await navigator.clipboard.writeText(markdown);
      setCopyStatus("Da sao chep bao cao Markdown.");
    } catch {
      setCopyStatus("Khong the sao chep tu dong trong moi truong hien tai.");
    }
  }

  return (
    <main className="app-shell">
      <Header state={viewState} />

      <section className="triage-board" aria-label="VYVY investigation workspace">
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

        <InvestigationColumn
          fastWarning={fastWarning}
          investigation={investigation}
          isLoading={isLoading}
          isReportVisible={isReportVisible}
          progress={progress}
          state={viewState}
        />

        <ReportColumn
          copyStatus={copyStatus}
          errorMessage={errorMessage}
          investigation={investigation}
          isError={isError}
          isLoading={isLoading}
          isReportVisible={isReportVisible}
          state={viewState}
          onCopyReport={() => {
            void handleCopyReport();
          }}
        />
      </section>

      <Footer />
    </main>
  );
}

function Header({ state }: { state: DemoViewState }) {
  return (
    <header className="topbar" aria-labelledby="page-title">
      <div className="brand-cluster">
        <div className="shield-mark" aria-hidden="true">
          V
        </div>
        <div>
          <h1 id="page-title">VYVY</h1>
          <p>AI Investigation &amp; Verification Engine</p>
        </div>
      </div>
      <p className="mission">Investigate. Debate. Verify. Explain.</p>
      <div className="system-status" aria-label={`Trang thai he thong: ${stateLabels[state]}`}>
        <span className={`status-dot status-${state}`} aria-hidden="true" />
        <span>Hệ thống: {stateLabels[state]}</span>
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
    <section className="column input-column" aria-labelledby="input-heading">
      <PanelHeader eyebrow="Nhập liệu điều tra" title="Nguồn cần kiểm tra" />

      <div className="chat-surface">
        <div className="message-bubble suspect">
          {inputText.trim() ? (
            <p>{shortPreview(inputText, 150)}</p>
          ) : (
            <p>Dán một đoạn chat, email hoặc nội dung đáng nghi để bắt đầu.</p>
          )}
        </div>
        <div className="time-stamp">14:20</div>
        <div className="message-bubble analyst">
          <p>
            {viewState === "empty"
              ? "Chưa có nội dung. Chọn ví dụ demo hoặc nhập văn bản để điều tra."
              : viewState === "loading"
                ? "Đang chạy Fast Check và điều tra đầy đủ. Báo cáo sẽ cập nhật khi backend trả về."
                : viewState === "error"
                  ? "Phát hiện lỗi đầu vào hoặc kết nối. Vui lòng xem thông báo ở cột báo cáo."
                  : "Đã sẵn sàng điều tra đa lớp. Nhấn phân tích để gọi API thật."}
          </p>
        </div>
        <div className="time-stamp">14:21</div>
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
        <span id="character-counter">{characterCount.toLocaleString("vi-VN")} / 12.000 ky tu</span>
        <span id="privacy-note">MVP chỉ nhận văn bản, không hỗ trợ upload.</span>
      </div>

      <label className="field-label" htmlFor="example-selector">
        Ví dụ demo
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

      {selectedCaseId ? (
        <div className="case-note">
          <strong>{selectedDemoCase?.description}</strong>
          <span>
            Dự kiến: Fast {riskLabels[selectedDemoCase?.expectedRiskBand.fast ?? "uncertain"]} / Full{" "}
            {riskLabels[selectedDemoCase?.expectedRiskBand.full ?? "uncertain"]}
          </span>
        </div>
      ) : null}

      <div className="button-row">
        <button className="primary-button" type="button" onClick={onAnalyze}>
          Phân tích bằng API
        </button>
        <button className="secondary-button" type="button" onClick={onClear}>
          Đặt lại
        </button>
      </div>

      <div className="safety-note" role="status">
        <strong>Cảnh báo rủi ro tức thì</strong>
        <span>Không chuyển tiền, không cung cấp mã OTP hoặc mật khẩu khi chưa xác minh.</span>
      </div>
    </section>
  );
}

function InvestigationColumn({
  fastWarning,
  investigation,
  isLoading,
  isReportVisible,
  progress,
  state,
}: {
  fastWarning: FastWarning;
  investigation: InvestigationResponse;
  isLoading: boolean;
  isReportVisible: boolean;
  progress: ProgressState[];
  state: DemoViewState;
}) {
  return (
    <section className="column investigation-column" aria-label="Investigation workspace">
      <div className="agent-strip" aria-label="Investigation agents">
        <AgentTile label="Tiếp nhận" value="Trích xuất nội dung" tone="purple" />
        <AgentTile label="Phân loại" value={riskLabels[fastWarning.risk_band] ?? fastWarning.risk_band} tone="blue" />
        <AgentTile label="Trạng thái" value={stateLabels[state]} tone="neutral" />
      </div>

      <div className="section-title-row">
        <StepMarker value="1" />
        <div>
          <h2>Sự thật &amp; bằng chứng</h2>
          <p>Hệ thống phân tích đa nguồn theo từng bước</p>
        </div>
      </div>

      <div className="two-up">
        <FastWarningCard fastWarning={fastWarning} state={state} />
        <ProgressCard progress={progress} state={state} />
      </div>

      <div className="section-title-row">
        <StepMarker value="2" />
        <div>
          <h2>Phân tích tâm lý</h2>
          <p>Nhận diện kỹ thuật thao túng</p>
        </div>
      </div>

      <BehavioralCard investigation={investigation} visible={isReportVisible} />

      <VerificationCard investigation={investigation} isLoading={isLoading} visible={isReportVisible} />
    </section>
  );
}

function ReportColumn({
  copyStatus,
  errorMessage,
  investigation,
  isError,
  isLoading,
  isReportVisible,
  state,
  onCopyReport,
}: {
  copyStatus: string;
  errorMessage: string;
  investigation: InvestigationResponse;
  isError: boolean;
  isLoading: boolean;
  isReportVisible: boolean;
  state: DemoViewState;
  onCopyReport: () => void;
}) {
  return (
    <aside className="column report-column" aria-labelledby="report-heading">
      <PanelHeader eyebrow="Bao cao ket luan" title="Ket qua xac minh" />
      <ConclusionCard
        errorMessage={errorMessage}
        investigation={investigation}
        isError={isError}
        isLoading={isLoading}
        isReportVisible={isReportVisible}
        state={state}
      />
      <EvidenceCard investigation={investigation} visible={isReportVisible} />
      <RecommendationsCard
        copyStatus={copyStatus}
        investigation={investigation}
        visible={isReportVisible}
        onCopyReport={onCopyReport}
      />
      <LimitationsCard investigation={investigation} state={state} visible={isReportVisible} />
    </aside>
  );
}

function PanelHeader({ eyebrow, title }: { eyebrow: string; title: string }) {
  return (
    <div className="panel-header">
      <span className="header-icon" aria-hidden="true" />
      <div>
        <p>{eyebrow}</p>
        <h2>{title}</h2>
      </div>
    </div>
  );
}

function AgentTile({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: "blue" | "neutral" | "purple";
}) {
  return (
    <div className={`agent-tile agent-${tone}`}>
      <span aria-hidden="true" />
      <div>
        <strong>{label}</strong>
        <p>{value}</p>
      </div>
    </div>
  );
}

function StepMarker({ value }: { value: string }) {
  return (
    <span className="step-marker" aria-hidden="true">
      {value}
    </span>
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
    <section className="work-card" aria-labelledby="fast-warning-heading">
      <div className="card-title-row">
        <h3 id="fast-warning-heading">Fast Check</h3>
        <RiskBadge label={fastWarning.risk_band} score={fastWarning.score} />
      </div>
      <p className="card-summary">
        {isWaitingForFastCheck ? "Dang chay /api/v1/fast-check..." : fastWarning.message}
      </p>
      <ul className="flag-list" aria-label="Top red flags">
        {topFlags.length > 0 ? (
          topFlags.map((flag) => (
            <li key={flag.code}>
              <strong>{flag.label}</strong>
              <span>{flag.evidence_span}</span>
            </li>
          ))
        ) : (
          <li>Chua co red flag trong trang thai hien tai.</li>
        )}
      </ul>
      <p className="mini-meta">
        {isWaitingForFastCheck
          ? "Dang cho Fast Check."
          : state === "loading"
            ? "Dang tiep tuc Full Investigation."
            : `Latency: ${fastWarning.latency_ms}ms`}
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
    <section className="work-card" aria-labelledby="progress-heading">
      <div className="card-title-row">
        <h3 id="progress-heading">Tien trinh</h3>
        <span className={`state-chip chip-${state}`}>{stateLabels[state]}</span>
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
  const score = investigation.behavioral_analysis?.behavioral_risk_score;

  return (
    <section className="work-card behavioral-card" aria-labelledby="behavior-heading">
      <div className="card-title-row">
        <h3 id="behavior-heading">Behavioral Analysis</h3>
        <span className="metric-chip">{typeof score === "number" ? `${formatScore(score)}/100` : "N/A"}</span>
      </div>
      {!visible ? (
        <p className="empty-copy">Chua co phan tich hanh vi.</p>
      ) : (
        <>
          <div className="behavior-grid">
            {behavioralFlags.length > 0 ? (
              behavioralFlags.slice(0, 4).map((flag) => (
                <div className={`behavior-tile severity-${flag.severity}`} key={`${flag.type}-${flag.evidence_span}`}>
                  <strong>{behavioralLabels[flag.type] ?? flag.type}</strong>
                  <span>{flag.severity}</span>
                </div>
              ))
            ) : (
              <div className="behavior-tile calm">
                <strong>Khong co tin hieu</strong>
                <span>low</span>
              </div>
            )}
          </div>
          <p className="card-summary">{behavioralSummary(investigation)}</p>
          <ul className="compact-list">
            {behavioralFlags.map((flag) => (
              <li key={`${flag.type}-${flag.evidence_span}`}>
                <strong>{flag.evidence_span}</strong>
                <span>{flag.explanation}</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}

function VerificationCard({
  investigation,
  isLoading,
  visible,
}: {
  investigation: InvestigationResponse;
  isLoading: boolean;
  visible: boolean;
}) {
  const consensus = expertConsensus(investigation);
  const experts = expertDetails(investigation);

  return (
    <section className="judge-card" aria-labelledby="judge-heading">
      <div className="section-title-row">
        <StepMarker value="3" />
        <div>
          <h2 id="judge-heading">Xac thuc tong hop</h2>
          <p>Judge Agent tong hop tu bang chung, chuyen gia, ngu canh va tam ly</p>
        </div>
      </div>

      {isLoading ? (
        <SkeletonBlock />
      ) : !visible ? (
        <p className="empty-copy">Chua co du lieu Judge Agent. Chay phan tich de tao bao cao.</p>
      ) : (
        <>
          <div className="weight-grid">
            <MetricTile label="Rui ro" value={`${formatScore(riskScore(investigation))}/100`} />
            <MetricTile label="Tin cay" value={`${formatScore(confidenceScore(investigation))}/100`} />
            <MetricTile label="Dong thuan" value={`${formatScore(consensus.consensus_score)}/100`} />
            <MetricTile label="Evidence" value={String(investigation.evidence?.length ?? 0)} />
            <MetricTile label="Tong latency" value={`${investigation.timings_ms.total ?? 0}ms`} />
          </div>
          <div className="expert-list">
            {experts.length > 0 ? (
              experts.map((expert) => (
                <details key={expert.expert}>
                  <summary>
                    <span>{expertLabels[expert.expert] ?? expert.expert}</span>
                    <strong>{formatScore(displayScore(expert))}/100</strong>
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
              ))
            ) : (
              <p className="empty-copy">Backend chua tra danh sach chuyen gia.</p>
            )}
          </div>
        </>
      )}
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
      <section className="report-block" aria-labelledby="report-heading">
        <StateBanner tone="error" title="Khong the hien thi ket qua" message={errorMessage || "Backend khong tra bao cao co the hien thi."} />
      </section>
    );
  }

  if (isLoading) {
    return (
      <section className="report-block loading-panel" aria-labelledby="report-heading">
        <StateBanner tone="loading" title="Dang tao bao cao" message="Dang cho /api/v1/investigate tra ket qua." />
        <SkeletonBlock />
      </section>
    );
  }

  if (!isReportVisible) {
    return (
      <section className="report-block" aria-labelledby="report-heading">
        <StateBanner
          tone="empty"
          title="Chua co bao cao"
          message={
            state === "typing"
              ? "Noi dung da san sang. Nhan Phan tich de chay API that."
              : "Chon vi du hoac nhap van ban de bat dau demo text-only."
          }
        />
      </section>
    );
  }

  return (
    <section className="report-block" aria-labelledby="report-heading">
      <div className="score-stack">
        <RiskMeter label={riskLabel(investigation)} score={riskScore(investigation)} />
        <div className="confidence-box">
          <span>{formatScore(confidenceScore(investigation))}/100</span>
          <strong>Do tin cay AI</strong>
        </div>
      </div>
      <h3 id="report-heading">{investigation.report.conclusion ?? "Bao cao chua co ket luan."}</h3>
      <ul className="reason-list">
        {reportWhy(investigation).map((reason) => (
          <li key={reason}>{reason}</li>
        ))}
      </ul>
      <EvidenceModeBadge status={investigation.evidence_status} />
    </section>
  );
}

function StateBanner({
  message,
  title,
  tone,
}: {
  message: string;
  title: string;
  tone: "empty" | "error" | "loading";
}) {
  return (
    <div className={`state-banner ${tone}`} role={tone === "error" ? "alert" : "status"}>
      <strong>{title}</strong>
      <span>{message}</span>
    </div>
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
  const status = investigation.evidence_status;

  return (
    <section className="report-block" aria-labelledby="evidence-heading">
      <div className="card-title-row">
        <h3 id="evidence-heading">Bang chung noi bat</h3>
        <EvidenceModeBadge status={status} />
      </div>
      {!visible ? (
        <p className="empty-copy">Bang chung se xuat hien sau khi backend tra bao cao.</p>
      ) : evidence.length === 0 ? (
        <div className="no-evidence">
          <strong>Khong co bang chung ngoai</strong>
          <span>UI van hien thi bao cao dua tren input, experts va canh bao cua backend.</span>
        </div>
      ) : (
        <ol className="evidence-list">
          {evidence.slice(0, 5).map((item) => (
            <EvidenceRow item={item} key={item.evidence_id} />
          ))}
        </ol>
      )}
      {visible && status?.errors && status.errors.length > 0 ? (
        <ul className="error-list">
          {status.errors.map((error) => (
            <li key={error}>{error}</li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}

function EvidenceRow({ item }: { item: EvidenceItem }) {
  return (
    <li className="evidence-row">
      <span className="evidence-index" aria-hidden="true" />
      <div>
        <a href={item.url} rel="noreferrer" target="_blank">
          {item.title}
        </a>
        <p>{item.snippet}</p>
        <dl>
          <div>
            <dt>Nguon</dt>
            <dd>{item.source_name}</dd>
          </div>
          <div>
            <dt>Credibility</dt>
            <dd>{formatScore(item.credibility_score)}/100</dd>
          </div>
          <div>
            <dt>Relevance</dt>
            <dd>{formatScore(item.relevance_score)}/100</dd>
          </div>
        </dl>
      </div>
    </li>
  );
}

function EvidenceModeBadge({ status }: { status: InvestigationResponse["evidence_status"] }) {
  const mode = status?.mode ?? "disabled";
  const label = mode === "mock" ? "Mock evidence" : mode === "live" ? "Live evidence" : mode;

  return (
    <span className={`source-badge source-${mode}`} title={`Provider: ${status?.provider ?? "unavailable"}`}>
      {label}
    </span>
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
    <section className="report-block" aria-labelledby="recommendation-heading">
      <h3 id="recommendation-heading">Khuyen nghi hanh dong</h3>
      {!visible ? (
        <p className="empty-copy">Khuyen nghi se hien thi sau khi bao cao san sang.</p>
      ) : (
        <ul className="action-grid">
          {recommendedActions(investigation).map((action) => (
            <li key={action}>{action}</li>
          ))}
        </ul>
      )}
      <button className="primary-button full-width" type="button" onClick={onCopyReport}>
        Xuat bao cao Markdown
      </button>
      {copyStatus ? (
        <p className="mini-meta" role="status">
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
        "Giao dien se goi API that khi nhan Phan tich.",
        "MVP khong ho tro OCR, anh, PDF, upload file, dang nhap hoac co so du lieu.",
        `Trang thai hien tai: ${stateLabels[state]}.`,
      ];

  return (
    <section className="report-block small" aria-labelledby="limitation-heading">
      <h3 id="limitation-heading">Gioi han</h3>
      <ul className="limitation-list">
        {limitations.map((limitation) => (
          <li key={limitation}>{limitation}</li>
        ))}
      </ul>
      {visible ? (
        <p className="mini-meta">
          Provider: {investigation.evidence_status?.provider ?? "unavailable"} · Results:{" "}
          {investigation.evidence_status?.results_returned ?? 0}
        </p>
      ) : null}
    </section>
  );
}

function RiskBadge({ label, score }: { label: string; score: number }) {
  return (
    <span className={`risk-badge risk-${label}`}>
      {riskLabels[label] ?? label} · {formatScore(score)}
    </span>
  );
}

function RiskMeter({ label, score }: { label: string; score: number }) {
  return (
    <div className={`risk-meter meter-${label}`} aria-label={`Rui ro ${formatScore(score)} tren 100`}>
      <span>{formatScore(score)}</span>
      <strong>{riskLabels[label] ?? label}</strong>
      <small>Rui ro / 100</small>
    </div>
  );
}

function MetricTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-tile">
      <span>{value}</span>
      <strong>{label}</strong>
    </div>
  );
}

function SkeletonBlock() {
  return (
    <div className="skeleton-block" aria-hidden="true">
      <span />
      <span />
      <span />
    </div>
  );
}

function Footer() {
  return (
    <footer className="footer-strip">
      <span>Safety First</span>
      <span>Pydantic Validated</span>
      <span>Deterministic Score</span>
    </footer>
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
    pending: "Cho",
    active: "Dang chay",
    done: "Xong",
    partial: "Mot phan",
    error: "Loi",
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
    "Backend chua cung cap danh sach ly do chi tiet.",
  ]);
}

function recommendedActions(investigation: InvestigationResponse): string[] {
  const safetyAdvice = investigation.safety_advice;
  const safetyActions =
    isRecord(safetyAdvice) && Array.isArray(safetyAdvice.actions)
      ? safetyAdvice.actions
      : undefined;
  return nonEmptyStrings(investigation.report.actions ?? safetyActions, [
    "Xac minh qua kenh chinh thuc truoc khi hanh dong.",
  ]);
}

function reportLimitations(investigation: InvestigationResponse): string[] {
  return [
    ...nonEmptyStrings(investigation.report.limitations, [
      "Frontend hien thi cac truong backend cung cap; mot so phan co the thieu khi ket qua partial.",
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
        text: "Khong co chi tiet ly do tu backend.",
        evidence_ids: expert.cited_evidence_ids,
      },
    ];
  }
  return expert.reasons
    .filter(isRecord)
    .map((reason) => ({
      text: typeof reason.text === "string" ? reason.text : "Ly do khong co noi dung.",
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
  return investigation.behavioral_analysis?.summary ?? "Backend chua cung cap tom tat hanh vi.";
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

function formatScore(value: number): string {
  if (!Number.isFinite(value)) {
    return "0";
  }
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function nextFrame(): Promise<void> {
  return new Promise((resolve) => {
    window.requestAnimationFrame(() => resolve());
  });
}
