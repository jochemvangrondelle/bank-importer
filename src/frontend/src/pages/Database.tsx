import { useState, useEffect } from "react";
import {
  Card,
  Button,
  Space,
  message,
  Typography,
  Alert,
  Statistic,
  Row,
  Col,
  Popconfirm,
} from "antd";
import {
  DatabaseOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
} from "@ant-design/icons";
import axiosInstance from "../utils/axios";
import { API_CONFIG } from "../config/settings";

const { Title, Text } = Typography;

export const Database = () => {
  const [initializing, setInitializing] = useState(false);
  const [cleaning, setCleaning] = useState(false);
  const [stats, setStats] = useState<any>(null);

  const handleInit = async (reset: boolean = false) => {
    try {
      setInitializing(true);
      await axiosInstance.post(`${API_CONFIG.ENDPOINTS.DATABASE}/init`, {
        reset,
      });
      message.success(
        reset
          ? "Database reset successfully"
          : "Database initialized successfully"
      );
      loadStats();
    } catch (error: any) {
      message.error("Failed to initialize database");
    } finally {
      setInitializing(false);
    }
  };

  const handleClean = async (
    outputOnly: boolean = false,
    dbOnly: boolean = false
  ) => {
    try {
      setCleaning(true);
      await axiosInstance.post(`${API_CONFIG.ENDPOINTS.DATABASE}/clean`, {
        output_only: outputOnly,
        db_only: dbOnly,
      });
      message.success("Cleanup completed successfully");
      loadStats();
    } catch (error: any) {
      message.error("Failed to clean database");
    } finally {
      setCleaning(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await axiosInstance.get(
        `${API_CONFIG.ENDPOINTS.DATABASE}/stats`
      );
      setStats(response.data);
    } catch (error: any) {
      // Stats might not be available
      console.error("Failed to load database stats", error);
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  return (
    <div style={{ padding: "24px" }}>
      <Card>
        <Space direction="vertical" size="large" style={{ width: "100%" }}>
          <Title level={2}>
            <DatabaseOutlined /> Database Management
          </Title>

          {stats && (
            <Card title="Database Statistics">
              <Row gutter={16}>
                <Col span={8}>
                  <Statistic
                    title="Total Transactions"
                    value={stats.total_transactions || 0}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="Total Accounts"
                    value={stats.total_accounts || 0}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="Import Sessions"
                    value={stats.total_import_sessions || 0}
                  />
                </Col>
              </Row>
            </Card>
          )}

          <Card title="Initialize Database">
            <Space direction="vertical" size="middle">
              <Text>
                Initialize the database schema. Use reset to drop existing
                tables and recreate them.
              </Text>
              <Space>
                <Button
                  type="primary"
                  icon={<CheckCircleOutlined />}
                  onClick={() => handleInit(false)}
                  loading={initializing}
                >
                  Initialize
                </Button>
                <Popconfirm
                  title="Reset Database"
                  description="This will delete all data. Are you sure?"
                  onConfirm={() => handleInit(true)}
                  okText="Yes"
                  cancelText="No"
                >
                  <Button danger loading={initializing}>
                    Reset Database
                  </Button>
                </Popconfirm>
              </Space>
            </Space>
          </Card>

          <Card title="Clean Database">
            <Space direction="vertical" size="middle">
              <Text>
                Clean output directories and/or database. This will remove
                exported files and optionally clear the database.
              </Text>
              <Space>
                <Button
                  icon={<DeleteOutlined />}
                  onClick={() => handleClean(true, false)}
                  loading={cleaning}
                >
                  Clean Output Only
                </Button>
                <Popconfirm
                  title="Clean Database"
                  description="This will delete all database records. Are you sure?"
                  onConfirm={() => handleClean(false, true)}
                  okText="Yes"
                  cancelText="No"
                >
                  <Button danger loading={cleaning}>
                    Clean Database Only
                  </Button>
                </Popconfirm>
                <Popconfirm
                  title="Clean All"
                  description="This will delete both output files and database records. Are you sure?"
                  onConfirm={() => handleClean(false, false)}
                  okText="Yes"
                  cancelText="No"
                >
                  <Button danger loading={cleaning}>
                    Clean All
                  </Button>
                </Popconfirm>
              </Space>
            </Space>
          </Card>

          <Alert
            message="Warning"
            description="Database operations are irreversible. Please make sure you have backups before performing reset or clean operations."
            type="warning"
            showIcon
          />
        </Space>
      </Card>
    </div>
  );
};
