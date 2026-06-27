import type {
  FastCheckFlag,
  FastCheckResponse,
  EvidenceItem,
  ExpertAssessment,
  InvestigationResponse,
  InvestigationStatus,
  RiskLabel,
} from "../types";

export type DemoViewState = "empty" | "typing" | "loading" | "completed" | "partial" | "error";

export type ProgressState = "pending" | "active" | "done" | "partial" | "error";

export type FastWarningFlag = FastCheckFlag;

export type FastWarning = FastCheckResponse;

export interface EvidenceStatus {
  provider: string;
  mode: "mock" | "live" | "disabled" | "failed";
  operation_status: "completed" | "partial" | "disabled";
  success: boolean;
  queries_attempted: number;
  results_returned: number;
  errors: string[];
}

export interface BehavioralRedFlag {
  type: string;
  severity: "low" | "medium" | "high";
  evidence_span: string;
  explanation: string;
}

export interface BehavioralAnalysis {
  red_flags: BehavioralRedFlag[];
  behavioral_risk_score: number;
  summary: string;
}

export interface ExpertReason {
  text: string;
  basis: "evidence" | "input_text";
  evidence_ids: string[];
  input_text_span: string | null;
}

export interface DemoExpertAssessment extends ExpertAssessment {
  expert: "financial" | "legal_risk" | "cyber" | "osint";
  score: number;
  verdict: "low_risk" | "uncertain" | "suspicious" | "high_risk";
  reasons: ExpertReason[];
  missing_information: string[];
  confidence: number;
  warnings: string[];
}

export interface ExpertConsensusReport {
  consensus_score: number;
  consensus_label: "safe" | "uncertain" | "suspicious" | "high_risk";
  supported_findings: string[];
  disagreements: string[];
  missing_evidence: string[];
}

export interface StructuredReport extends Record<string, unknown> {
  status: InvestigationStatus;
  conclusion: string;
  risk_score: number;
  risk_label: RiskLabel;
  confidence_score: number;
  why: string[];
  expert_consensus: ExpertConsensusReport;
  behavioral_red_flags: BehavioralRedFlag[];
  actions: string[];
  limitations: string[];
  markdown: string;
}

export interface DemoInvestigationResponse extends InvestigationResponse {
  status: InvestigationStatus;
  evidence: EvidenceItem[];
  experts: DemoExpertAssessment[];
  evidence_status: EvidenceStatus;
  behavioral_analysis: BehavioralAnalysis;
  safety_advice: {
    actions: string[];
    warnings: string[];
    note: string;
  };
  report: StructuredReport;
}

export interface DemoCase {
  id: string;
  label: string;
  description: string;
  expectedRiskBand: {
    fast: FastWarning["risk_band"];
    full: RiskLabel;
  };
  text: string;
  defaultState: "completed" | "partial";
  fastWarning: FastWarning;
  investigation: DemoInvestigationResponse;
}

const bankEvidence: EvidenceItem[] = [
  {
    evidence_id: "mock_bank_otp_advisory",
    title: "[MOCK] Kịch bản giả mạo ngân hàng yêu cầu OTP",
    url: "https://vyvy-mock.example/evidence/mock_bank_otp_advisory",
    source_name: "VYVY Mock Evidence — Bank Safety Lab",
    published_at: "2026-06-01",
    snippet:
      "Mock evidence: kịch bản demo mô tả tin nhắn yêu cầu OTP, mật khẩu hoặc mã xác thực.",
    retrieved_at: "2026-06-27T10:00:00+07:00",
    credibility_score: 45,
    relevance_score: 94,
  },
  {
    evidence_id: "mock_account_lock_script",
    title: "[MOCK] Mẫu đe dọa khóa tài khoản trong tin nhắn",
    url: "https://vyvy-mock.example/evidence/mock_account_lock_script",
    source_name: "VYVY Mock Evidence — Account Safety Lab",
    published_at: "2026-06-01",
    snippet:
      "Mock evidence: kịch bản demo ghi nhận đe dọa khóa tài khoản để thúc ép xác minh gấp.",
    retrieved_at: "2026-06-27T10:00:00+07:00",
    credibility_score: 45,
    relevance_score: 89,
  },
];

const bankExperts: DemoExpertAssessment[] = [
  expert("cyber", 88, "high_risk", ["mock_bank_otp_advisory"], [
    "Yêu cầu OTP là tín hiệu chiếm quyền tài khoản.",
    "Đường dẫn trong tin nhắn cần được xác minh độc lập.",
  ]),
  expert("financial", 82, "high_risk", ["mock_bank_otp_advisory"], [
    "Tin nhắn tạo áp lực xác minh gấp trước khi kiểm tra kênh chính thức.",
  ]),
  expert("legal_risk", 76, "suspicious", ["mock_account_lock_script"], [
    "Cách đe dọa khóa tài khoản không đủ cơ sở để xem là quy trình chính thức.",
  ]),
  expert("osint", 84, "high_risk", ["mock_account_lock_script"], [
    "Mock evidence cho thấy mô-típ tương tự cảnh báo an toàn tài khoản.",
  ]),
];

const bankBehavioral: BehavioralAnalysis = {
  red_flags: [
    {
      type: "urgency",
      severity: "high",
      evidence_span: "gấp trong 10 phút",
      explanation: "Tạo áp lực thời gian khiến người nhận khó kiểm tra lại.",
    },
    {
      type: "fear",
      severity: "high",
      evidence_span: "tài khoản sẽ bị khóa",
      explanation: "Dùng nỗi sợ mất quyền truy cập tài khoản để thúc ép hành động.",
    },
  ],
  behavioral_risk_score: 72,
  summary: "Có dấu hiệu thao túng bằng áp lực thời gian và nỗi sợ mất tài khoản.",
};

const bankReport: StructuredReport = {
  status: "completed",
  conclusion:
    "Nội dung có nhiều dấu hiệu nguy cơ cao. Chưa đủ cơ sở để kết luận chắc chắn, nên cần xác minh độc lập.",
  risk_score: 82.7,
  risk_label: "high_risk",
  confidence_score: 78.8,
  why: [
    "Tin nhắn yêu cầu cung cấp OTP/mã xác thực.",
    "Có đe dọa khóa tài khoản để tạo áp lực.",
    "Mock evidence trùng với mô-típ tin nhắn giả mạo ngân hàng trong fixture demo.",
  ],
  expert_consensus: {
    consensus_score: 83.1,
    consensus_label: "high_risk",
    supported_findings: [
      "Yêu cầu OTP là tín hiệu rủi ro tài khoản.",
      "Mô-típ đe dọa khóa tài khoản được mock evidence hỗ trợ.",
    ],
    disagreements: [
      "Legal Risk thận trọng hơn vì chưa xác minh được danh tính người gửi.",
    ],
    missing_evidence: ["Chưa xác minh được chủ sở hữu thật của đường dẫn."],
  },
  behavioral_red_flags: bankBehavioral.red_flags,
  actions: [
    "Không cung cấp OTP, mật khẩu, PIN hoặc mã xác thực.",
    "Không bấm đường dẫn lạ; hãy tự nhập địa chỉ website chính thức nếu cần.",
    "Liên hệ ngân hàng qua ứng dụng hoặc tổng đài chính thức.",
    "Lưu lại tin nhắn, số gửi và thời điểm nhận để đối chiếu.",
  ],
  limitations: [
    "Đây là dữ liệu mock cho demo, không phải kết quả xác minh trực tiếp.",
    "Báo cáo này không phải tư vấn pháp lý.",
    "Không kết luận cá nhân/tổ chức là tội phạm.",
  ],
  markdown:
    "# Báo cáo xác minh VYVY\n\n## Kết luận\nNội dung có nhiều dấu hiệu nguy cơ cao.\n",
};

const partialBehavioral: BehavioralAnalysis = {
  red_flags: [
    {
      type: "reciprocity",
      severity: "medium",
      evidence_span: "đặt cọc nhỏ",
      explanation: "Yêu cầu khoản nhỏ trước có thể dẫn tới cam kết lớn hơn.",
    },
    {
      type: "scarcity",
      severity: "medium",
      evidence_span: "giữ suất",
      explanation: "Gợi ý cơ hội có giới hạn để thúc ép quyết định nhanh.",
    },
  ],
  behavioral_risk_score: 46,
  summary: "Có dấu hiệu phí trước và khan hiếm, nhưng chưa thấy OTP hay link đăng nhập.",
};

const recruitmentEvidence: EvidenceItem[] = [
  {
    evidence_id: "mock_recruitment_fee_pattern",
    title: "[MOCK] Mẫu tuyển dụng yêu cầu phí bảo đảm",
    url: "https://vyvy-mock.example/evidence/mock_recruitment_fee_pattern",
    source_name: "VYVY Mock Evidence — Recruitment Lab",
    published_at: "2026-06-01",
    snippet:
      "Mock evidence: lời mời việc online yêu cầu chuyển phí hồ sơ, phí bảo đảm hoặc đặt cọc trước.",
    retrieved_at: "2026-06-27T10:00:00+07:00",
    credibility_score: 45,
    relevance_score: 92,
  },
];

const partialReport: StructuredReport = {
  status: "completed",
  conclusion:
    "Nội dung có dấu hiệu đáng nghi vì yêu cầu phí trước trong bối cảnh tuyển dụng. Cần xác minh độc lập trước khi phản hồi.",
  risk_score: 64.5,
  risk_label: "suspicious",
  confidence_score: 66.2,
  why: [
    "Nội dung nhắc đến đặt cọc/phí trước trong bối cảnh tuyển dụng.",
    "Có áp lực giữ suất trong ngày.",
    "Mock evidence hỗ trợ mô-típ tuyển dụng yêu cầu phí hoặc đặt cọc trước.",
  ],
  expert_consensus: {
    consensus_score: 59.4,
    consensus_label: "suspicious",
    supported_findings: ["Có yêu cầu phí/đặt cọc trước dựa trên nội dung và mock evidence."],
    disagreements: ["Cyber thấp hơn vì chưa có tín hiệu chiếm quyền tài khoản."],
    missing_evidence: ["Chưa có thông tin pháp nhân hoặc thông báo tuyển dụng chính thức."],
  },
  behavioral_red_flags: partialBehavioral.red_flags,
  actions: [
    "Chưa chuyển tiền đặt cọc hoặc phí hồ sơ trước khi xác minh.",
    "Yêu cầu hợp đồng, mã số doanh nghiệp và thông tin tuyển dụng công khai.",
    "Trao đổi với người thân hoặc người có kinh nghiệm tuyển dụng trước khi phản hồi.",
  ],
  limitations: [
    "Đây là dữ liệu mock cho demo, không phải kết quả xác minh trực tiếp.",
    "Báo cáo này không phải tư vấn pháp lý.",
    "Không kết luận cá nhân/tổ chức là tội phạm.",
  ],
  markdown:
    "# Báo cáo xác minh VYVY\n\n## Kết luận\nNội dung có dấu hiệu đáng nghi vì yêu cầu phí trước.\n",
};

const authorityEvidence: EvidenceItem[] = [
  {
    evidence_id: "mock_authority_payment_script",
    title: "[MOCK] Mẫu mạo danh thẩm quyền yêu cầu nộp tiền",
    url: "https://vyvy-mock.example/evidence/mock_authority_payment_script",
    source_name: "VYVY Mock Evidence — Authority Pressure Lab",
    published_at: "2026-06-01",
    snippet:
      "Mock evidence: kịch bản demo yêu cầu chuyển tiền vào tài khoản tạm giữ để chứng minh vô can.",
    retrieved_at: "2026-06-27T10:00:00+07:00",
    credibility_score: 45,
    relevance_score: 95,
  },
  {
    evidence_id: "mock_secrecy_pressure",
    title: "[MOCK] Yêu cầu giữ bí mật trong kịch bản gây áp lực",
    url: "https://vyvy-mock.example/evidence/mock_secrecy_pressure",
    source_name: "VYVY Mock Evidence — Behavioral Lab",
    published_at: "2026-06-01",
    snippet:
      "Mock evidence: lời yêu cầu không nói với người khác làm giảm khả năng người nhận nhờ kiểm tra.",
    retrieved_at: "2026-06-27T10:00:00+07:00",
    credibility_score: 45,
    relevance_score: 91,
  },
];

const authorityBehavioral: BehavioralAnalysis = {
  red_flags: [
    {
      type: "fear",
      severity: "high",
      evidence_span: "liên quan vụ án rửa tiền",
      explanation: "Tạo nỗi sợ hậu quả pháp lý nghiêm trọng.",
    },
    {
      type: "urgency",
      severity: "high",
      evidence_span: "trong 30 phút",
      explanation: "Ép quyết định nhanh khi người nhận chưa kịp xác minh.",
    },
    {
      type: "isolation",
      severity: "high",
      evidence_span: "Không được nói với ai",
      explanation: "Cô lập người nhận khỏi nguồn hỗ trợ bên ngoài.",
    },
  ],
  behavioral_risk_score: 88,
  summary: "Tín hiệu thao túng hành vi rất mạnh: sợ hãi, khẩn cấp, cô lập và chuyển tiền.",
};

const authorityExperts: DemoExpertAssessment[] = [
  expert("legal_risk", 92, "high_risk", ["mock_authority_payment_script"], [
    "Yêu cầu chuyển tiền để chứng minh vô can là dấu hiệu rủi ro cao.",
  ]),
  expert("financial", 90, "high_risk", ["mock_authority_payment_script"], [
    "Khoản chuyển 25 triệu bị thúc ép trong thời gian ngắn.",
  ]),
  expert("cyber", 72, "suspicious", [], [
    "Không thấy link kỹ thuật, nhưng có kịch bản ép hành động nguy hiểm.",
  ]),
  expert("osint", 86, "high_risk", ["mock_secrecy_pressure"], [
    "Mock evidence hỗ trợ tín hiệu giữ bí mật và gây áp lực.",
  ]),
];

const authorityReport: StructuredReport = {
  status: "completed",
  conclusion:
    "Nội dung có dấu hiệu nguy cơ cao vì kết hợp đe dọa pháp lý, chuyển tiền gấp và cô lập người nhận.",
  risk_score: 90.4,
  risk_label: "high_risk",
  confidence_score: 74.6,
  why: [
    "Tin nhắn đe dọa liên quan vụ án.",
    "Có yêu cầu chuyển tiền vào tài khoản tạm giữ.",
    "Có yêu cầu giữ bí mật, làm giảm khả năng xác minh độc lập.",
  ],
  expert_consensus: {
    consensus_score: 87.8,
    consensus_label: "high_risk",
    supported_findings: [
      "Yêu cầu chuyển tiền gấp được hỗ trợ bởi mock evidence.",
      "Yêu cầu giữ bí mật là tín hiệu thao túng hành vi mạnh.",
    ],
    disagreements: ["Cyber tập trung vào rủi ro tài khoản nên thấp hơn các chuyên gia khác."],
    missing_evidence: ["Chưa xác minh danh tính người gửi hoặc số tài khoản nhận tiền."],
  },
  behavioral_red_flags: authorityBehavioral.red_flags,
  actions: [
    "Không chuyển tiền.",
    "Không tiếp tục cung cấp thông tin cá nhân qua cuộc trò chuyện này.",
    "Gọi đến kênh chính thức của cơ quan/tổ chức liên quan nếu cần xác minh.",
    "Lưu lại nội dung và nhờ người tin cậy kiểm tra cùng.",
  ],
  limitations: [
    "Đây là dữ liệu mock cho demo, không phải kết quả xác minh trực tiếp.",
    "Báo cáo này không phải tư vấn pháp lý.",
    "Không kết luận cá nhân/tổ chức là tội phạm.",
  ],
  markdown:
    "# Báo cáo xác minh VYVY\n\n## Kết luận\nNội dung có dấu hiệu nguy cơ cao vì có đe dọa, chuyển tiền gấp và giữ bí mật.\n",
};

const marketplaceEvidence: EvidenceItem[] = [
  {
    evidence_id: "mock_marketplace_login_pattern",
    title: "[MOCK] Mẫu đường dẫn đăng nhập nhận tiền trên sàn mua bán",
    url: "https://vyvy-mock.example/evidence/mock_marketplace_login_pattern",
    source_name: "VYVY Mock Evidence — Marketplace Lab",
    published_at: "2026-06-01",
    snippet:
      "Mock evidence: tin nhắn demo thúc giục người bán đăng nhập qua đường dẫn để nhận tiền.",
    retrieved_at: "2026-06-27T10:00:00+07:00",
    credibility_score: 45,
    relevance_score: 88,
  },
];

const marketplaceBehavioral: BehavioralAnalysis = {
  red_flags: [
    {
      type: "urgency",
      severity: "medium",
      evidence_span: "hết hạn sau 15 phút",
      explanation: "Áp lực thời gian có thể làm người bán bỏ qua bước kiểm tra.",
    },
    {
      type: "authority_pressure",
      severity: "medium",
      evidence_span: "Người mua trên DemoMarket đã thanh toán",
      explanation: "Tạo cảm giác giao dịch đã được hệ thống xác nhận.",
    },
  ],
  behavioral_risk_score: 42,
  summary: "Có áp lực thời gian và link đăng nhập, nhưng nội dung chưa yêu cầu OTP hoặc chuyển tiền.",
};

const marketplaceExperts: DemoExpertAssessment[] = [
  expert("cyber", 66, "suspicious", ["mock_marketplace_login_pattern"], [
    "Link đăng nhập nhận tiền cần được xác minh độc lập.",
  ]),
  expert("financial", 42, "uncertain", [], [
    "Chưa có yêu cầu chuyển tiền trực tiếp trong nội dung đầu vào.",
  ]),
  expert("legal_risk", 35, "uncertain", [], [
    "Chưa đủ dữ liệu về điều khoản giao dịch hoặc danh tính người mua.",
  ]),
  expert("osint", 48, "uncertain", ["mock_marketplace_login_pattern"], [
    "Fixture mock chỉ hỗ trợ mô-típ chung, chưa xác minh link cụ thể.",
  ]),
];

const marketplaceReport: StructuredReport = {
  status: "partial",
  conclusion:
    "Kết quả một phần: nội dung có dấu hiệu đáng nghi, nhưng còn thiếu dữ liệu để đánh giá chắc chắn.",
  risk_score: 49.8,
  risk_label: "uncertain",
  confidence_score: 45.1,
  why: [
    "Có đường dẫn đăng nhập để nhận tiền.",
    "Có áp lực hết hạn nhanh.",
    "Mock evidence hỗ trợ mô-típ marketplace, nhưng thiếu dữ liệu xác minh chủ sở hữu link.",
  ],
  expert_consensus: {
    consensus_score: 48.1,
    consensus_label: "uncertain",
    supported_findings: ["Có link đăng nhập nhận tiền và áp lực thời gian."],
    disagreements: ["Cyber đánh giá cao hơn vì trọng tâm là rủi ro đăng nhập."],
    missing_evidence: ["Thiếu xác minh domain/link và lịch sử giao dịch trong ứng dụng chính thức."],
  },
  behavioral_red_flags: marketplaceBehavioral.red_flags,
  actions: [
    "Không nhập tài khoản/mật khẩu qua link trong tin nhắn.",
    "Kiểm tra giao dịch trong app hoặc website chính thức.",
    "Nếu chưa chắc, liên hệ hỗ trợ chính thức của nền tảng trước khi xử lý đơn.",
  ],
  limitations: [
    "Demo partial: còn thiếu xác minh domain/link cụ thể.",
    "Báo cáo này không phải tư vấn pháp lý.",
    "Không kết luận cá nhân/tổ chức là tội phạm.",
  ],
  markdown:
    "# Báo cáo xác minh VYVY\n\n## Kết luận\nKết quả một phần: link nhận tiền cần được xác minh độc lập.\n",
};

const benignEvidence: EvidenceItem[] = [
  {
    evidence_id: "mock_benign_survey_reference",
    title: "[MOCK] Tham chiếu nhắc khảo sát môn học không yêu cầu thông tin nhạy cảm",
    url: "https://vyvy-mock.example/evidence/mock_benign_survey_reference",
    source_name: "VYVY Mock Evidence — Benign Reference Lab",
    published_at: "2026-06-01",
    snippet:
      "Mock evidence: thông báo demo chỉ nhắc hoàn thành khảo sát và không yêu cầu tiền, mật khẩu hoặc OTP.",
    retrieved_at: "2026-06-27T10:00:00+07:00",
    credibility_score: 45,
    relevance_score: 82,
  },
];

const benignBehavioral: BehavioralAnalysis = {
  red_flags: [],
  behavioral_risk_score: 4,
  summary: "Không phát hiện tín hiệu thao túng hành vi đáng kể trong nội dung demo.",
};

const benignExperts: DemoExpertAssessment[] = [
  expert("cyber", 6, "low_risk", [], ["Không thấy link đáng ngờ hoặc yêu cầu thông tin đăng nhập."]),
  expert("financial", 4, "low_risk", [], ["Không có yêu cầu chuyển tiền hoặc phí trước."]),
  expert("legal_risk", 8, "low_risk", [], [
    "Không có đe dọa pháp lý hoặc yêu cầu hành động nguy hiểm.",
  ]),
  expert("osint", 10, "low_risk", ["mock_benign_survey_reference"], [
    "Mock evidence là tham chiếu lành tính cho nội dung khảo sát.",
  ]),
];

const benignReport: StructuredReport = {
  status: "completed",
  conclusion:
    "Nội dung có vẻ rủi ro thấp trong phạm vi dữ liệu mock: không có yêu cầu tiền, OTP, mật khẩu hoặc tải ứng dụng.",
  risk_score: 8.4,
  risk_label: "low",
  confidence_score: 69.5,
  why: [
    "Không có yêu cầu OTP, mật khẩu, PIN hoặc chuyển tiền.",
    "Không có đe dọa, bí mật hoặc áp lực tài chính.",
    "Mock evidence là tham chiếu lành tính cho thông báo khảo sát.",
  ],
  expert_consensus: {
    consensus_score: 7.1,
    consensus_label: "safe",
    supported_findings: ["Không phát hiện tín hiệu lừa đảo chính trong nội dung đầu vào."],
    disagreements: [],
    missing_evidence: ["Nếu nghi ngờ, người dùng vẫn nên kiểm tra trong cổng thông tin quen thuộc."],
  },
  behavioral_red_flags: benignBehavioral.red_flags,
  actions: [
    "Nếu cần thực hiện, mở cổng thông tin quen thuộc theo cách thường dùng.",
    "Không chia sẻ mật khẩu/OTP nếu có yêu cầu phát sinh ngoài nội dung này.",
  ],
  limitations: [
    "Đây là dữ liệu mock cho demo, không phải kết quả xác minh trực tiếp.",
    "Báo cáo này không phải tư vấn pháp lý.",
    "Không kết luận cá nhân/tổ chức là tội phạm.",
  ],
  markdown:
    "# Báo cáo xác minh VYVY\n\n## Kết luận\nNội dung có vẻ rủi ro thấp trong phạm vi dữ liệu mock.\n",
};

function exampleInput(
  id: string,
  label: string,
  description: string,
  text: string,
  expectedRiskBand: DemoCase["expectedRiskBand"],
  template: Pick<DemoCase, "defaultState" | "fastWarning" | "investigation">,
): DemoCase {
  return {
    id,
    label,
    description,
    text,
    expectedRiskBand,
    defaultState: template.defaultState,
    fastWarning: {
      ...template.fastWarning,
      request_id: `demo-fast-${id}`,
    },
    investigation: {
      ...template.investigation,
      investigation_id: `demo-${id}`,
    },
  };
}

export const demoCases: DemoCase[] = [
  {
    id: "bank-otp-phishing",
    label: "Ngân hàng Demo yêu cầu OTP",
    description: "Tin nhắn synthetic mạo danh ngân hàng, có đường dẫn và áp lực khóa tài khoản.",
    expectedRiskBand: { fast: "critical", full: "high_risk" },
    text:
      "Ngân hàng VYBank Demo thông báo tài khoản sẽ bị khóa. Vui lòng cung cấp OTP tại " +
      "https://vybank-demo.example/login để xác minh gấp trong 10 phút.",
    defaultState: "completed",
    fastWarning: {
      request_id: "demo-fast-bank-otp",
      risk_band: "critical",
      score: 95,
      triggered_flags: [
        {
          code: "OTP_REQUEST",
          label: "Yêu cầu cung cấp OTP",
          severity: "critical",
          evidence_span: "cung cấp OTP",
        },
        {
          code: "ACCOUNT_LOCK_OR_ARREST_THREAT",
          label: "Đe dọa khóa tài khoản",
          severity: "high",
          evidence_span: "tài khoản sẽ bị khóa",
        },
        {
          code: "SUSPICIOUS_LINK",
          label: "Đường dẫn cần xác minh",
          severity: "high",
          evidence_span: "https://vybank-demo.example/login",
        },
      ],
      message: "Nội dung có dấu hiệu nguy cơ chiếm quyền tài khoản.",
      immediate_actions: [
        "Không cung cấp OTP hoặc mật khẩu.",
        "Không bấm vào đường dẫn trong tin nhắn.",
        "Liên hệ ngân hàng qua kênh chính thức.",
      ],
      latency_ms: 118,
    },
    investigation: {
      investigation_id: "demo-bank-otp-phishing",
      status: "completed",
      evidence_status: {
        provider: "mock",
        mode: "mock",
        operation_status: "completed",
        success: true,
        queries_attempted: 1,
        results_returned: 2,
        errors: [],
      },
      evidence: bankEvidence,
      experts: bankExperts,
      behavioral_analysis: bankBehavioral,
      verification: {
        risk_score: bankReport.risk_score,
        risk_label: bankReport.risk_label,
        confidence_score: bankReport.confidence_score,
      },
      safety_advice: {
        actions: bankReport.actions,
        warnings: [],
        note: "Không đối đầu với người gửi; hãy xác minh qua kênh chính thức.",
      },
      report: bankReport,
      warnings: [],
      timings_ms: {
        fast_check: 118,
        evidence_search: 320,
        experts: 740,
        total: 1280,
      },
    },
  },
  {
    id: "recruitment-fee",
    label: "Tuyển dụng yêu cầu phí",
    description: "Tin tuyển dụng synthetic yêu cầu phí hồ sơ/đặt cọc trước khi nhận việc.",
    expectedRiskBand: { fast: "suspicious", full: "suspicious" },
    text:
      "JobBee Demo tuyển cộng tác viên online lương cao, không cần phỏng vấn. " +
      "Bạn chỉ cần chuyển phí hồ sơ 299.000đ hôm nay để giữ suất và nhận nhiệm vụ đầu tiên.",
    defaultState: "completed",
    fastWarning: {
      request_id: "demo-fast-recruitment",
      risk_band: "suspicious",
      score: 72,
      triggered_flags: [
        {
          code: "UPFRONT_FEE",
          label: "Yêu cầu phí/đặt cọc trước",
          severity: "high",
          evidence_span: "chuyển phí hồ sơ 299.000đ",
        },
        {
          code: "URGENT_MONEY_TRANSFER",
          label: "Thúc giục chuyển khoản",
          severity: "high",
          evidence_span: "hôm nay để giữ suất",
        },
      ],
      message: "Nội dung có dấu hiệu yêu cầu phí trước trong bối cảnh tuyển dụng.",
      immediate_actions: [
        "Chưa chuyển tiền đặt cọc hoặc phí hồ sơ.",
        "Xác minh đơn vị tuyển dụng qua nguồn chính thức.",
      ],
      latency_ms: 96,
    },
    investigation: {
      investigation_id: "demo-recruitment-fee",
      status: "completed",
      evidence_status: {
        provider: "mock",
        mode: "mock",
        operation_status: "completed",
        success: true,
        queries_attempted: 1,
        results_returned: 1,
        errors: [],
      },
      evidence: recruitmentEvidence,
      experts: [
        expert("financial", 68, "suspicious", ["mock_recruitment_fee_pattern"], [
          "Yêu cầu phí trước khi nhận việc là dấu hiệu cần thận trọng.",
        ]),
        expert("legal_risk", 54, "suspicious", ["mock_recruitment_fee_pattern"], [
          "Thiếu thông tin hợp đồng và danh tính đơn vị tuyển dụng.",
        ]),
        expert("cyber", 25, "uncertain", [], ["Chưa thấy đường dẫn hoặc yêu cầu OTP."]),
        expert("osint", 58, "suspicious", ["mock_recruitment_fee_pattern"], [
          "Fixture mock cho thấy mô-típ tương tự các lời mời việc online yêu cầu phí.",
        ]),
      ],
      behavioral_analysis: partialBehavioral,
      verification: {
        risk_score: partialReport.risk_score,
        risk_label: partialReport.risk_label,
        confidence_score: partialReport.confidence_score,
      },
      safety_advice: {
        actions: partialReport.actions,
        warnings: [],
        note: "Không phải tư vấn pháp lý; hãy xác minh độc lập.",
      },
      report: partialReport,
      warnings: [],
      timings_ms: {
        fast_check: 96,
        evidence_search: 300,
        experts: 680,
        total: 1180,
      },
    },
  },
  {
    id: "fake-authority-payment",
    label: "Mạo danh thẩm quyền",
    description: "Tin nhắn synthetic gây sợ hãi, yêu cầu chuyển tiền vào tài khoản tạm giữ và giữ bí mật.",
    expectedRiskBand: { fast: "critical", full: "high_risk" },
    text:
      "Tổ xác minh hồ sơ Demo thông báo bạn liên quan vụ án rửa tiền. " +
      "Phải chuyển 25 triệu vào tài khoản tạm giữ trong 30 phút để chứng minh vô can. Không được nói với ai.",
    defaultState: "completed",
    fastWarning: {
      request_id: "demo-fast-authority",
      risk_band: "critical",
      score: 98,
      triggered_flags: [
        {
          code: "ACCOUNT_LOCK_OR_ARREST_THREAT",
          label: "Đe dọa bắt giữ/vụ án",
          severity: "critical",
          evidence_span: "liên quan vụ án rửa tiền",
        },
        {
          code: "URGENT_MONEY_TRANSFER",
          label: "Yêu cầu chuyển tiền gấp",
          severity: "critical",
          evidence_span: "chuyển 25 triệu",
        },
        {
          code: "SECRECY_REQUEST",
          label: "Yêu cầu giữ bí mật",
          severity: "high",
          evidence_span: "Không được nói với ai",
        },
      ],
      message: "Nội dung có nhiều dấu hiệu nguy cơ cao: đe dọa, chuyển tiền gấp và yêu cầu giữ bí mật.",
      immediate_actions: [
        "Không chuyển tiền vào tài khoản được cung cấp trong tin nhắn.",
        "Dừng trao đổi và xác minh qua kênh chính thức.",
        "Báo cho người thân hoặc người tin cậy trước khi hành động.",
      ],
      latency_ms: 104,
    },
    investigation: {
      investigation_id: "demo-fake-authority-payment",
      status: "completed",
      evidence_status: {
        provider: "mock",
        mode: "mock",
        operation_status: "completed",
        success: true,
        queries_attempted: 1,
        results_returned: 2,
        errors: [],
      },
      evidence: authorityEvidence,
      experts: authorityExperts,
      behavioral_analysis: authorityBehavioral,
      verification: {
        risk_score: authorityReport.risk_score,
        risk_label: authorityReport.risk_label,
        confidence_score: authorityReport.confidence_score,
      },
      safety_advice: {
        actions: authorityReport.actions,
        warnings: [],
        note: "Không phải tư vấn pháp lý; hãy xác minh độc lập.",
      },
      report: authorityReport,
      warnings: [],
      timings_ms: {
        fast_check: 104,
        evidence_search: 330,
        experts: 720,
        total: 1270,
      },
    },
  },
  {
    id: "marketplace-login-link",
    label: "Sàn mua bán gửi link nhận tiền",
    description: "Tin nhắn synthetic có link đăng nhập nhận tiền, áp lực hết hạn và thông tin còn thiếu.",
    expectedRiskBand: { fast: "suspicious", full: "uncertain" },
    text:
      "Người mua trên DemoMarket đã thanh toán. Người bán cần đăng nhập tại " +
      "https://pay-demomarket.example/claim để nhận tiền, giao dịch sẽ hết hạn sau 15 phút.",
    defaultState: "partial",
    fastWarning: {
      request_id: "demo-fast-marketplace",
      risk_band: "suspicious",
      score: 69,
      triggered_flags: [
        {
          code: "SUSPICIOUS_LINK",
          label: "Đường dẫn cần xác minh",
          severity: "high",
          evidence_span: "https://pay-demomarket.example/claim",
        },
        {
          code: "URGENCY",
          label: "Áp lực thời gian",
          severity: "medium",
          evidence_span: "hết hạn sau 15 phút",
        },
      ],
      message: "Nội dung có link đăng nhập nhận tiền và áp lực thời gian; cần xác minh kênh chính thức.",
      immediate_actions: [
        "Không đăng nhập qua đường dẫn trong tin nhắn.",
        "Mở ứng dụng/sàn chính thức bằng cách tự nhập địa chỉ hoặc dùng app đã cài.",
      ],
      latency_ms: 88,
    },
    investigation: {
      investigation_id: "demo-marketplace-login-link",
      status: "partial",
      evidence_status: {
        provider: "mock",
        mode: "mock",
        operation_status: "partial",
        success: true,
        queries_attempted: 1,
        results_returned: 1,
        errors: [],
      },
      evidence: marketplaceEvidence,
      experts: marketplaceExperts,
      behavioral_analysis: marketplaceBehavioral,
      verification: {
        risk_score: marketplaceReport.risk_score,
        risk_label: marketplaceReport.risk_label,
        confidence_score: marketplaceReport.confidence_score,
      },
      safety_advice: {
        actions: marketplaceReport.actions,
        warnings: ["Demo partial: còn thiếu xác minh domain/link cụ thể."],
        note: "Không phải tư vấn pháp lý; hãy xác minh độc lập.",
      },
      report: marketplaceReport,
      warnings: ["Demo partial: còn thiếu xác minh domain/link cụ thể."],
      timings_ms: {
        fast_check: 88,
        evidence_search: 900,
        experts: 690,
        total: 1580,
      },
    },
  },
  {
    id: "benign-school-reminder",
    label: "Nhắc khảo sát môn học",
    description: "Tin nhắn synthetic lành tính, không yêu cầu tiền, OTP, mật khẩu hay link lạ.",
    expectedRiskBand: { fast: "low", full: "low" },
    text:
      "Trường Demo nhắc sinh viên hoàn thành khảo sát môn học trước thứ Sáu trên cổng thông tin quen thuộc. " +
      "Thông báo không yêu cầu mật khẩu, OTP, chuyển tiền hoặc tải ứng dụng.",
    defaultState: "completed",
    fastWarning: {
      request_id: "demo-fast-benign",
      risk_band: "low",
      score: 5,
      triggered_flags: [],
      message: "Không thấy tín hiệu lừa đảo rõ ràng trong nội dung demo này.",
      immediate_actions: ["Vẫn kiểm tra thông báo trong kênh quen thuộc nếu có nghi ngờ."],
      latency_ms: 74,
    },
    investigation: {
      investigation_id: "demo-benign-school-reminder",
      status: "completed",
      evidence_status: {
        provider: "mock",
        mode: "mock",
        operation_status: "completed",
        success: true,
        queries_attempted: 1,
        results_returned: 1,
        errors: [],
      },
      evidence: benignEvidence,
      experts: benignExperts,
      behavioral_analysis: benignBehavioral,
      verification: {
        risk_score: benignReport.risk_score,
        risk_label: benignReport.risk_label,
        confidence_score: benignReport.confidence_score,
      },
      safety_advice: {
        actions: benignReport.actions,
        warnings: [],
        note: "Không phải tư vấn pháp lý; hãy xác minh độc lập.",
      },
      report: benignReport,
      warnings: [],
      timings_ms: {
        fast_check: 74,
        evidence_search: 260,
        experts: 610,
        total: 1090,
      },
    },
  },
  exampleInput(
    "telegram-tiktok-vip",
    "Like TikTok — phí kích hoạt VIP",
    "Lừa đảo việc làm online trên Telegram: trả thưởng ban đầu, sau đó yêu cầu chuyển trước để nhận nhiệm vụ VIP.",
    [
      "Em được một người trên Telegram mời làm việc online.",
      "Công việc là like video TikTok và chụp màn hình gửi lại.",
      "Ngày đầu em kiếm được 300.000 đồng.",
      "Sau đó họ bảo muốn nhận nhiệm vụ VIP thì phải chuyển trước 2 triệu để kích hoạt tài khoản.",
      "Họ nói sẽ hoàn lại tiền sau 15 phút.",
    ].join("\n"),
    { fast: "suspicious", full: "high_risk" },
    {
      defaultState: "completed",
      fastWarning: {
        request_id: "placeholder",
        risk_band: "suspicious",
        score: 78,
        triggered_flags: [
          {
            code: "UPFRONT_FEE",
            label: "Yêu cầu chuyển tiền trước",
            severity: "high",
            evidence_span: "chuyển trước 2 triệu",
          },
          {
            code: "URGENT_MONEY_TRANSFER",
            label: "Hứa hoàn tiền trong thời gian rất ngắn",
            severity: "high",
            evidence_span: "hoàn lại tiền sau 15 phút",
          },
        ],
        message: "Nội dung có dấu hiệu lừa đảo việc làm online yêu cầu nộp tiền trước.",
        immediate_actions: [
          "Không chuyển thêm tiền để kích hoạt VIP hoặc nâng cấp tài khoản.",
          "Dừng làm nhiệm vụ và không tiếp tục liên lạc nếu bị ép chuyển khoản.",
        ],
        latency_ms: 92,
      },
      investigation: {
        investigation_id: "placeholder",
        status: "completed",
        evidence_status: {
          provider: "mock",
          mode: "mock",
          operation_status: "completed",
          success: true,
          queries_attempted: 1,
          results_returned: 1,
          errors: [],
        },
        evidence: recruitmentEvidence,
        experts: [
          expert("financial", 74, "high_risk", ["mock_recruitment_fee_pattern"], [
            "Mô-típ trả thưởng nhỏ ban đầu rồi yêu cầu nộp tiền lớn hơn là dấu hiệu đáng ngờ.",
          ]),
          expert("legal_risk", 58, "suspicious", [], [
            "Thiếu thông tin pháp nhân và hợp đồng lao động rõ ràng.",
          ]),
          expert("cyber", 32, "uncertain", [], ["Chưa thấy yêu cầu OTP hay link đăng nhập."]),
          expert("osint", 66, "suspicious", ["mock_recruitment_fee_pattern"], [
            "Fixture mock cho thấy mô-típ việc online yêu cầu phí kích hoạt tương tự.",
          ]),
        ],
        behavioral_analysis: partialBehavioral,
        verification: {
          risk_score: 76.2,
          risk_label: "high_risk",
          confidence_score: 64.5,
        },
        safety_advice: {
          actions: [
            "Không chuyển thêm tiền để kích hoạt VIP.",
            "Chụp lại hội thoại và báo cho ngân hàng nếu đã chuyển tiền.",
          ],
          warnings: [],
          note: "Không phải tư vấn pháp lý; hãy xác minh độc lập.",
        },
        report: {
          ...partialReport,
          risk_score: 76.2,
          risk_label: "high_risk",
          conclusion:
            "Nội dung có dấu hiệu nguy cơ cao vì kết hợp việc làm online, thưởng ban đầu và yêu cầu chuyển tiền trước.",
        },
        warnings: [],
        timings_ms: { fast_check: 92, evidence_search: 310, experts: 700, total: 1200 },
      },
    },
  ),
  exampleInput(
    "coin-investment-ponzi",
    "Đầu tư coin lợi nhuận 3%/ngày",
    "Lời mời đầu tư tiền ảo với lợi nhuận cao bất thường và hoa hồng giới thiệu — dấu hiệu mô hình Ponzi.",
    [
      "Một người bạn giới thiệu em đầu tư vào dự án coin mới.",
      "Họ cam kết lợi nhuận 3% mỗi ngày.",
      "Nếu giới thiệu thêm người tham gia em sẽ được hoa hồng.",
      "Hiện đã có hơn 5.000 người tham gia.",
    ].join("\n"),
    { fast: "suspicious", full: "high_risk" },
    {
      defaultState: "completed",
      fastWarning: {
        request_id: "placeholder",
        risk_band: "suspicious",
        score: 81,
        triggered_flags: [
          {
            code: "UNREALISTIC_RETURN",
            label: "Lợi nhuận cao bất thường",
            severity: "high",
            evidence_span: "lợi nhuận 3% mỗi ngày",
          },
          {
            code: "REFERRAL_PRESSURE",
            label: "Khuyến khích giới thiệu thêm người",
            severity: "medium",
            evidence_span: "giới thiệu thêm người tham gia",
          },
        ],
        message: "Nội dung có dấu hiệu đầu tư lợi nhuận cao bất thường và mô hình giới thiệu.",
        immediate_actions: [
          "Không chuyển tiền vào dự án chưa xác minh được giấy phép và pháp nhân.",
          "Tra cứu độc lập tên dự án trước khi tham gia.",
        ],
        latency_ms: 88,
      },
      investigation: {
        investigation_id: "placeholder",
        status: "completed",
        evidence_status: {
          provider: "mock",
          mode: "mock",
          operation_status: "completed",
          success: true,
          queries_attempted: 1,
          results_returned: 1,
          errors: [],
        },
        evidence: recruitmentEvidence,
        experts: [
          expert("financial", 88, "high_risk", [], [
            "Lợi nhuận 3%/ngày vượt xa mức hợp lý của đầu tư thông thường.",
          ]),
          expert("legal_risk", 62, "suspicious", [], [
            "Chưa có thông tin giấy phép hoạt động hoặc cơ quan quản lý.",
          ]),
          expert("cyber", 28, "uncertain", [], ["Chưa thấy yêu cầu thông tin đăng nhập trực tiếp."]),
          expert("osint", 70, "suspicious", [], [
            "Con số 5.000 người tham gia chưa được xác minh độc lập.",
          ]),
        ],
        behavioral_analysis: partialBehavioral,
        verification: {
          risk_score: 79.5,
          risk_label: "high_risk",
          confidence_score: 61.0,
        },
        safety_advice: {
          actions: [
            "Không đầu tư thêm vào dự án chưa xác minh.",
            "Cảnh báo người thân nếu bạn giới thiệu tiếp tục tham gia.",
          ],
          warnings: [],
          note: "Không phải tư vấn pháp lý; hãy xác minh độc lập.",
        },
        report: {
          ...partialReport,
          risk_score: 79.5,
          risk_label: "high_risk",
          conclusion:
            "Nội dung có dấu hiệu nguy cơ cao vì cam kết lợi nhuận cao bất thường và mô hình giới thiệu.",
        },
        warnings: [],
        timings_ms: { fast_check: 88, evidence_search: 320, experts: 710, total: 1220 },
      },
    },
  ),
  exampleInput(
    "romance-customs-gift",
    "Người yêu online + phí hải quan nhận quà",
    "Lừa đảo tình cảm kết hợp mạo danh hải quan yêu cầu đóng phí để nhận quà từ người nước ngoài.",
    [
      "Em quen một người nước ngoài trên Facebook được 2 tuần.",
      "Người đó nói yêu em và muốn gửi quà về Việt Nam.",
      "Sau đó có người tự nhận là nhân viên hải quan gọi điện bảo em đóng 15 triệu tiền thuế để nhận quà.",
    ].join("\n"),
    { fast: "critical", full: "high_risk" },
    {
      defaultState: "completed",
      fastWarning: {
        request_id: "placeholder",
        risk_band: "critical",
        score: 94,
        triggered_flags: [
          {
            code: "URGENT_MONEY_TRANSFER",
            label: "Yêu cầu chuyển tiền để nhận quà",
            severity: "critical",
            evidence_span: "đóng 15 triệu tiền thuế",
          },
          {
            code: "FAKE_AUTHORITY",
            label: "Mạo danh cơ quan thẩm quyền",
            severity: "high",
            evidence_span: "nhân viên hải quan",
          },
        ],
        message: "Nội dung có dấu hiệu lừa đảo tình cảm kết hợp yêu cầu nộp phí giả mạo.",
        immediate_actions: [
          "Không chuyển tiền phí thuế hay phí hải quan qua điện thoại.",
          "Liên hệ cơ quan hải quan qua kênh chính thức nếu cần xác minh.",
        ],
        latency_ms: 98,
      },
      investigation: {
        investigation_id: "placeholder",
        status: "completed",
        evidence_status: {
          provider: "mock",
          mode: "mock",
          operation_status: "completed",
          success: true,
          queries_attempted: 1,
          results_returned: 2,
          errors: [],
        },
        evidence: authorityEvidence,
        experts: authorityExperts,
        behavioral_analysis: authorityBehavioral,
        verification: {
          risk_score: authorityReport.risk_score,
          risk_label: authorityReport.risk_label,
          confidence_score: authorityReport.confidence_score,
        },
        safety_advice: {
          actions: authorityReport.actions,
          warnings: [],
          note: "Không phải tư vấn pháp lý; hãy xác minh độc lập.",
        },
        report: authorityReport,
        warnings: [],
        timings_ms: { fast_check: 98, evidence_search: 340, experts: 730, total: 1280 },
      },
    },
  ),
  exampleInput(
    "cheap-iphone-prepay",
    "iPhone giá rẻ — chuyển khoản trước",
    "Fanpage bán điện thoại giá quá thấp, yêu cầu chuyển khoản toàn bộ và không hỗ trợ COD.",
    [
      "Em thấy một fanpage bán iPhone 16 Pro Max giá 12 triệu.",
      "Shop yêu cầu chuyển khoản trước toàn bộ.",
      "Họ nói vì giá khuyến mãi nên không hỗ trợ COD.",
    ].join("\n"),
    { fast: "suspicious", full: "suspicious" },
    {
      defaultState: "partial",
      fastWarning: {
        request_id: "placeholder",
        risk_band: "suspicious",
        score: 74,
        triggered_flags: [
          {
            code: "UPFRONT_FEE",
            label: "Yêu cầu thanh toán trước toàn bộ",
            severity: "high",
            evidence_span: "chuyển khoản trước toàn bộ",
          },
          {
            code: "UNREALISTIC_OFFER",
            label: "Giá bán bất thường so với thị trường",
            severity: "high",
            evidence_span: "iPhone 16 Pro Max giá 12 triệu",
          },
        ],
        message: "Nội dung có dấu hiệu bán hàng giá quá rẻ và yêu cầu chuyển khoản trước.",
        immediate_actions: [
          "Không chuyển khoản trước cho shop chưa xác minh.",
          "Ưu tiên mua qua sàn hoặc cửa hàng có địa chỉ rõ ràng.",
        ],
        latency_ms: 85,
      },
      investigation: {
        investigation_id: "placeholder",
        status: "partial",
        evidence_status: {
          provider: "mock",
          mode: "mock",
          operation_status: "partial",
          success: true,
          queries_attempted: 1,
          results_returned: 1,
          errors: [],
        },
        evidence: marketplaceEvidence,
        experts: marketplaceExperts,
        behavioral_analysis: marketplaceBehavioral,
        verification: {
          risk_score: marketplaceReport.risk_score,
          risk_label: marketplaceReport.risk_label,
          confidence_score: marketplaceReport.confidence_score,
        },
        safety_advice: {
          actions: marketplaceReport.actions,
          warnings: ["Chưa xác minh được danh tính fanpage/shop."],
          note: "Không phải tư vấn pháp lý; hãy xác minh độc lập.",
        },
        report: marketplaceReport,
        warnings: ["Chưa xác minh được danh tính fanpage/shop."],
        timings_ms: { fast_check: 85, evidence_search: 880, experts: 680, total: 1550 },
      },
    },
  ),
  exampleInput(
    "zalo-investment-withdrawal-fee",
    "Đầu tư Zalo — phí xác minh để rút tiền",
    "Lừa đảo đầu tư: số dư tăng ảo trên app, nhưng yêu cầu nộp thêm phí mới được rút.",
    [
      "Chị gái em được một người trên Zalo giới thiệu đầu tư.",
      "Bỏ vào 50 triệu.",
      "Sau 2 tuần tài khoản hiển thị thành 120 triệu.",
      "Nhưng muốn rút tiền thì phải nộp thêm 15% phí xác minh.",
    ].join("\n"),
    { fast: "critical", full: "high_risk" },
    {
      defaultState: "completed",
      fastWarning: {
        request_id: "placeholder",
        risk_band: "critical",
        score: 96,
        triggered_flags: [
          {
            code: "UPFRONT_FEE",
            label: "Yêu cầu phí trước khi rút tiền",
            severity: "critical",
            evidence_span: "nộp thêm 15% phí xác minh",
          },
          {
            code: "UNREALISTIC_RETURN",
            label: "Lợi nhuận tăng bất thường",
            severity: "high",
            evidence_span: "50 triệu thành 120 triệu",
          },
        ],
        message: "Nội dung có dấu hiệu lừa đảo đầu tư: số dư ảo và yêu cầu nộp phí để rút.",
        immediate_actions: [
          "Không nộp thêm phí xác minh hoặc phí rút tiền.",
          "Liên hệ ngân hàng ngay nếu đã chuyển tiền đầu tư.",
        ],
        latency_ms: 102,
      },
      investigation: {
        investigation_id: "placeholder",
        status: "completed",
        evidence_status: {
          provider: "mock",
          mode: "mock",
          operation_status: "completed",
          success: true,
          queries_attempted: 1,
          results_returned: 2,
          errors: [],
        },
        evidence: authorityEvidence,
        experts: authorityExperts,
        behavioral_analysis: authorityBehavioral,
        verification: {
          risk_score: 91.8,
          risk_label: "high_risk",
          confidence_score: 72.4,
        },
        safety_advice: {
          actions: [
            "Không nộp thêm phí xác minh để rút tiền.",
            "Lưu lại giao dịch và báo ngân hàng nếu đã chuyển tiền.",
            "Trao đổi với người thân trước khi hành động tiếp.",
          ],
          warnings: [],
          note: "Không phải tư vấn pháp lý; hãy xác minh độc lập.",
        },
        report: {
          ...authorityReport,
          risk_score: 91.8,
          conclusion:
            "Nội dung có dấu hiệu nguy cơ cao vì lợi nhuận ảo trên app và yêu cầu nộp phí trước khi rút.",
        },
        warnings: [],
        timings_ms: { fast_check: 102, evidence_search: 350, experts: 750, total: 1310 },
      },
    },
  ),
];

export const progressStages = [
  "Understanding content",
  "Finding evidence",
  "Expert debate",
  "Judge verification",
  "Creating report",
] as const;

export function progressForState(state: DemoViewState): ProgressState[] {
  if (state === "completed") {
    return ["done", "done", "done", "done", "done"];
  }
  if (state === "partial") {
    return ["done", "partial", "done", "done", "done"];
  }
  if (state === "loading") {
    return ["done", "active", "pending", "pending", "pending"];
  }
  if (state === "error") {
    return ["done", "error", "pending", "pending", "pending"];
  }
  return ["pending", "pending", "pending", "pending", "pending"];
}

export function emptyFastWarning(): FastWarning {
  return {
    request_id: "empty",
    risk_band: "low",
    score: 0,
    triggered_flags: [],
    message: "Chưa chạy Fast Check. Chọn ví dụ hoặc nhập văn bản để xem cảnh báo nhanh.",
    immediate_actions: ["Không có hành động khẩn cấp trong trạng thái trống."],
    latency_ms: 0,
  };
}

export function errorFastWarning(): FastWarning {
  return {
    request_id: "error",
    risk_band: "high_risk",
    score: 0,
    triggered_flags: [],
    message: "Không thể tạo cảnh báo nhanh trong trạng thái lỗi demo.",
    immediate_actions: ["Thử đặt lại form hoặc chọn ví dụ khác."],
    latency_ms: 0,
  };
}

function expert(
  role: DemoExpertAssessment["expert"],
  score: number,
  verdict: DemoExpertAssessment["verdict"],
  citedEvidenceIds: string[],
  reasonTexts: string[],
): DemoExpertAssessment {
  return {
    expert: role,
    score,
    verdict,
    reasons: reasonTexts.map((text, index) => ({
      text,
      basis: citedEvidenceIds[index] ? "evidence" : "input_text",
      evidence_ids: citedEvidenceIds[index] ? [citedEvidenceIds[index]] : [],
      input_text_span: citedEvidenceIds[index] ? null : "nội dung đầu vào",
    })),
    cited_evidence_ids: citedEvidenceIds,
    missing_information: ["Cần xác minh thêm bằng nguồn chính thức nếu người dùng tiếp tục giao dịch."],
    confidence: citedEvidenceIds.length > 0 ? 78 : 42,
    warnings: [],
  };
}
