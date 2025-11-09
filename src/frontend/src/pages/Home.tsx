import { Card, Typography, Space, Button } from "antd";
import { useNavigate } from "react-router-dom";
import { APP_CONFIG } from "../config/settings";

const { Title, Paragraph } = Typography;

export const Home = () => {
  const navigate = useNavigate();

  return (
    <div style={{ padding: "24px" }}>
      <Space direction="vertical" size="large" style={{ width: "100%" }}>
        <Card>
          <Space direction="vertical" size="middle">
            <Title level={2}>Welcome to {APP_CONFIG.NAME}</Title>
            <Paragraph>
              A web-based interface for importing and managing bank
              transactions.
            </Paragraph>
            <Paragraph>
              <strong>Status:</strong> Foundation setup complete. Ready for
              feature development.
            </Paragraph>
            <Space>
              <Button type="primary" onClick={() => navigate("/import")}>
                Start Import Wizard
              </Button>
              <Button onClick={() => navigate("/status")}>View Status</Button>
            </Space>
          </Space>
        </Card>

        <Card title="Quick Links">
          <Space direction="vertical" style={{ width: "100%" }}>
            <Button
              type="link"
              block
              style={{ textAlign: "left" }}
              onClick={() => navigate("/import")}
            >
              📥 Import Wizard: Upload and parse bank statements
            </Button>
            <Button
              type="link"
              block
              style={{ textAlign: "left" }}
              onClick={() => navigate("/transactions")}
            >
              💳 Transactions: View and search all transactions
            </Button>
            <Button
              type="link"
              block
              style={{ textAlign: "left" }}
              onClick={() => navigate("/export")}
            >
              📤 Export: Export transactions to CSV/YAML
            </Button>
            <Button
              type="link"
              block
              style={{ textAlign: "left" }}
              onClick={() => navigate("/status")}
            >
              📊 Status: View account status and transaction statistics
            </Button>
            <Button
              type="link"
              block
              style={{ textAlign: "left" }}
              onClick={() => navigate("/pipeline")}
            >
              🚀 Run Pipeline: Execute full workflow (import → export)
            </Button>
            <Button
              type="link"
              block
              style={{ textAlign: "left" }}
              onClick={() => navigate("/configuration")}
            >
              ⚙️ Configuration: Manage accounts, targets, and settings
            </Button>
            <Button
              type="link"
              block
              style={{ textAlign: "left" }}
              onClick={() => navigate("/translation")}
            >
              🌐 Translation: Manage translation service and cache
            </Button>
            <Button
              type="link"
              block
              style={{ textAlign: "left" }}
              onClick={() => navigate("/database")}
            >
              🗄️ Database: Initialize, clean, and manage database
            </Button>
            <Button
              type="link"
              block
              style={{ textAlign: "left" }}
              onClick={() => navigate("/parsers")}
            >
              📄 Parsers: View available bank statement parsers
            </Button>
          </Space>
        </Card>
      </Space>
    </div>
  );
};
