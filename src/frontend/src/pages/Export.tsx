import { useState, useEffect } from "react";
import {
  Card,
  Button,
  Space,
  message,
  Table,
  Typography,
  Select,
  Tag,
  Alert,
} from "antd";
import {
  DownloadOutlined,
  ExportOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from "@ant-design/icons";
import axiosInstance from "../utils/axios";
import { API_CONFIG } from "../config/settings";
import type { ColumnsType } from "antd/es/table";

const { Title, Text } = Typography;
const { Option } = Select;

interface ExportSession {
  id: number;
  target_name: string;
  status: string;
  created_at: string;
  completed_at?: string;
  file_path?: string;
  error_message?: string;
}

interface Target {
  name: string;
  type: string;
  enabled: boolean;
}

export const Export = () => {
  const [targets, setTargets] = useState<Target[]>([]);
  const [selectedTarget, setSelectedTarget] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [sessions, setSessions] = useState<ExportSession[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTargets();
    loadSessions();
  }, []);

  const loadTargets = async () => {
    try {
      const response = await axiosInstance.get(
        API_CONFIG.ENDPOINTS.CONFIG.BASE
      );
      setTargets(response.data.targets || []);
    } catch (error: any) {
      message.error("Failed to load export targets");
    }
  };

  const loadSessions = async () => {
    try {
      setLoading(true);
      const response = await axiosInstance.get(
        API_CONFIG.ENDPOINTS.EXPORT.SESSIONS
      );
      setSessions(response.data.sessions || []);
    } catch (error: any) {
      message.error("Failed to load export sessions");
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      setExporting(true);
      await axiosInstance.post(API_CONFIG.ENDPOINTS.EXPORT.BASE, {
        target_name: selectedTarget || undefined,
      });
      message.success("Export job started successfully");
      // Refresh sessions after a short delay
      setTimeout(() => {
        loadSessions();
      }, 2000);
    } catch (error: any) {
      message.error("Failed to start export job");
    } finally {
      setExporting(false);
    }
  };

  const handleDownload = (filePath: string) => {
    // Create download link
    const link = document.createElement("a");
    link.href = `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.EXPORT.BASE}/download?file_path=${encodeURIComponent(filePath)}`;
    link.download = filePath.split("/").pop() || "export";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getStatusTag = (status: string) => {
    switch (status.toLowerCase()) {
      case "completed":
        return (
          <Tag color="green" icon={<CheckCircleOutlined />}>
            Completed
          </Tag>
        );
      case "failed":
        return (
          <Tag color="red" icon={<CloseCircleOutlined />}>
            Failed
          </Tag>
        );
      case "processing":
        return <Tag color="blue">Processing</Tag>;
      default:
        return <Tag>{status}</Tag>;
    }
  };

  const columns: ColumnsType<ExportSession> = [
    {
      title: "ID",
      dataIndex: "id",
      key: "id",
      width: 80,
    },
    {
      title: "Target",
      dataIndex: "target_name",
      key: "target_name",
    },
    {
      title: "Status",
      dataIndex: "status",
      key: "status",
      render: (status: string) => getStatusTag(status),
    },
    {
      title: "Created At",
      dataIndex: "created_at",
      key: "created_at",
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: "Completed At",
      dataIndex: "completed_at",
      key: "completed_at",
      render: (date: string | undefined) =>
        date ? new Date(date).toLocaleString() : "-",
    },
    {
      title: "File",
      dataIndex: "file_path",
      key: "file_path",
      render: (filePath: string | undefined, record: ExportSession) => {
        if (filePath && record.status === "completed") {
          return (
            <Button
              type="link"
              icon={<DownloadOutlined />}
              onClick={() => handleDownload(filePath)}
            >
              Download
            </Button>
          );
        }
        return "-";
      },
    },
    {
      title: "Error",
      dataIndex: "error_message",
      key: "error_message",
      render: (error: string | undefined) =>
        error ? <Text type="danger">{error}</Text> : "-",
    },
  ];

  const enabledTargets = targets.filter((t) => t.enabled);

  return (
    <div style={{ padding: "24px" }}>
      <Card>
        <Space direction="vertical" size="large" style={{ width: "100%" }}>
          <Title level={2}>
            <ExportOutlined /> Export Transactions
          </Title>

          <Card>
            <Space direction="vertical" size="middle" style={{ width: "100%" }}>
              <Text>
                Export transactions to configured targets. You can export to a
                specific target or to all enabled targets.
              </Text>
              <Space>
                <Select
                  placeholder="Select target (or leave empty for all enabled targets)"
                  style={{ width: 300 }}
                  allowClear
                  onChange={(value) => setSelectedTarget(value)}
                >
                  {enabledTargets.map((target) => (
                    <Option key={target.name} value={target.name}>
                      {target.name} ({target.type})
                    </Option>
                  ))}
                </Select>
                <Button
                  type="primary"
                  icon={<ExportOutlined />}
                  onClick={handleExport}
                  loading={exporting}
                  disabled={exporting}
                >
                  {selectedTarget
                    ? `Export to ${selectedTarget}`
                    : "Export to All Targets"}
                </Button>
              </Space>
              {enabledTargets.length === 0 && (
                <Alert
                  message="No enabled targets"
                  description="Please configure and enable at least one export target in the Configuration page."
                  type="warning"
                  showIcon
                />
              )}
            </Space>
          </Card>

          <Card title="Export History">
            <Table
              columns={columns}
              dataSource={sessions}
              rowKey="id"
              loading={loading}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showTotal: (total) => `Total ${total} sessions`,
              }}
            />
          </Card>
        </Space>
      </Card>
    </div>
  );
};
