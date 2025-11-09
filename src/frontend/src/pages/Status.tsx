import { useState, useEffect } from "react";
import {
  Card,
  Table,
  Typography,
  Space,
  Statistic,
  Row,
  Col,
  Alert,
  Spin,
  Tag,
} from "antd";
import {
  BankOutlined,
  TransactionOutlined,
  ImportOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from "@ant-design/icons";
import { API_CONFIG, UI_CONFIG } from "../config/settings";
import axiosInstance from "../utils/axios";
import type { ColumnsType } from "antd/es/table";

const { Title } = Typography;

interface AccountStatus {
  account_name: string;
  bank_name: string;
  account_number: string;
  parser: string | null;
  transaction_count: number;
  last_import: string | null; // ISO datetime string from API
  date_range: {
    min_date: string | null; // ISO date string from API
    max_date: string | null; // ISO date string from API
  };
}

interface AccountStatusSummary {
  total_accounts: number;
  total_transactions: number;
  total_import_sessions: number;
  completed_sessions: number;
  failed_sessions: number;
}

interface StatusResponse {
  accounts: AccountStatus[];
  summary: AccountStatusSummary;
  import_sessions: unknown[];
}

export const Status = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusData, setStatusData] = useState<StatusResponse | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await axiosInstance.get<StatusResponse>(
          API_CONFIG.ENDPOINTS.STATUS,
        );
        setStatusData(response.data);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load status",
        );
      } finally {
        setLoading(false);
      }
    };

    void fetchStatus();
  }, []);

  const formatDate = (dateStr: string | null): string => {
    if (!dateStr) return "Never";
    try {
      // Handle ISO datetime string
      const date = new Date(dateStr);
      if (Number.isNaN(date.getTime())) {
        return "Invalid date";
      }
      return date.toLocaleString(undefined, {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return "Invalid date";
    }
  };

  const formatDateRange = (
    dateRange: AccountStatus["date_range"],
  ): string => {
    if (!dateRange.min_date || !dateRange.max_date) {
      return "No transactions";
    }
    try {
      const minDate = new Date(dateRange.min_date);
      const maxDate = new Date(dateRange.max_date);
      const formatDateOnly = (d: Date): string =>
        d.toLocaleDateString(undefined, {
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
        });
      return `${formatDateOnly(minDate)} to ${formatDateOnly(maxDate)}`;
    } catch {
      return "Invalid date range";
    }
  };

  const columns: ColumnsType<AccountStatus> = [
    {
      title: "Account Name",
      dataIndex: "account_name",
      key: "account_name",
      sorter: (a, b) => a.account_name.localeCompare(b.account_name),
    },
    {
      title: "Bank",
      dataIndex: "bank_name",
      key: "bank_name",
      sorter: (a, b) => a.bank_name.localeCompare(b.bank_name),
    },
    {
      title: "Account Number",
      dataIndex: "account_number",
      key: "account_number",
    },
    {
      title: "Parser",
      dataIndex: "parser",
      key: "parser",
      render: (parser: string | null) =>
        parser ? <Tag color="blue">{parser}</Tag> : <Tag>Unknown</Tag>,
    },
    {
      title: "Transaction Count",
      dataIndex: "transaction_count",
      key: "transaction_count",
      sorter: (a, b) => a.transaction_count - b.transaction_count,
      align: "right",
      render: (count: number) => (
        <span style={{ fontWeight: "bold" }}>{count.toLocaleString()}</span>
      ),
    },
    {
      title: "Last Import",
      dataIndex: "last_import",
      key: "last_import",
      sorter: (a, b) => {
        if (!a.last_import && !b.last_import) return 0;
        if (!a.last_import) return 1;
        if (!b.last_import) return -1;
        const dateA = new Date(a.last_import).getTime();
        const dateB = new Date(b.last_import).getTime();
        if (Number.isNaN(dateA) || Number.isNaN(dateB)) return 0;
        return dateA - dateB;
      },
      render: (date: string | null) => formatDate(date),
    },
    {
      title: "Date Range",
      key: "date_range",
      render: (_: unknown, record: AccountStatus) =>
        formatDateRange(record.date_range),
    },
  ];

  if (loading) {
    return (
      <div style={{ padding: "24px", textAlign: "center" }}>
        <Spin size="large" />
        <div style={{ marginTop: "16px" }}>
          <Typography.Text>Loading status...</Typography.Text>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: "24px" }}>
        <Alert
          message="Error Loading Status"
          description={error}
          type="error"
          showIcon
        />
      </div>
    );
  }

  if (!statusData) {
    return (
      <div style={{ padding: "24px" }}>
        <Alert message="No status data available" type="warning" showIcon />
      </div>
    );
  }

  return (
    <div style={{ padding: "24px" }}>
      <Space direction="vertical" size="large" style={{ width: "100%" }}>
        <Card>
          <Title level={2}>
            <BankOutlined /> Account Status Overview
          </Title>
        </Card>

        <Card>
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} md={6}>
              <Statistic
                title="Total Accounts"
                value={statusData.summary.total_accounts}
                prefix={<BankOutlined />}
              />
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Statistic
                title="Total Transactions"
                value={statusData.summary.total_transactions}
                prefix={<TransactionOutlined />}
              />
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Statistic
                title="Import Sessions"
                value={statusData.summary.total_import_sessions}
                prefix={<ImportOutlined />}
              />
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Space direction="vertical" size="small">
                <Statistic
                  title="Completed"
                  value={statusData.summary.completed_sessions}
                  prefix={<CheckCircleOutlined style={{ color: "#52c41a" }} />}
                />
                <Statistic
                  title="Failed"
                  value={statusData.summary.failed_sessions}
                  prefix={<CloseCircleOutlined style={{ color: "#ff4d4f" }} />}
                />
              </Space>
            </Col>
          </Row>
        </Card>

        <Card title="Account Details">
          <Table
            columns={columns}
            dataSource={statusData.accounts}
            rowKey="account_name"
            pagination={{
              pageSize: UI_CONFIG.DEFAULT_PAGE_SIZE,
              showSizeChanger: true,
              showTotal: (total) => `Total ${total} accounts`,
            }}
            scroll={{ x: "max-content" }}
          />
        </Card>
      </Space>
    </div>
  );
};
