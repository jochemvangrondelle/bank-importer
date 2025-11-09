import { useState, useEffect } from "react";
import {
  Card,
  Table,
  Typography,
  Space,
  Tag,
  Descriptions,
  message,
} from "antd";
import { FileTextOutlined } from "@ant-design/icons";
import axiosInstance from "../utils/axios";
import { API_CONFIG } from "../config/settings";
import type { ColumnsType } from "antd/es/table";

const { Title, Text } = Typography;

interface ParserInfo {
  name: string;
  bank_type: string;
  supported_extensions: string[];
  description: string;
}

export const Parsers = () => {
  const [parsers, setParsers] = useState<ParserInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedParser, setSelectedParser] = useState<ParserInfo | null>(null);

  useEffect(() => {
    loadParsers();
  }, []);

  const loadParsers = async () => {
    try {
      setLoading(true);
      const response = await axiosInstance.get(API_CONFIG.ENDPOINTS.PARSERS);
      // API returns parsers grouped by bank_type
      const allParsers: ParserInfo[] = [];
      Object.values(response.data.parsers || {}).forEach((parserGroup: any) => {
        if (Array.isArray(parserGroup)) {
          allParsers.push(...parserGroup);
        }
      });
      setParsers(allParsers);
    } catch (error: any) {
      message.error("Failed to load parsers");
    } finally {
      setLoading(false);
    }
  };

  const columns: ColumnsType<ParserInfo> = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
      render: (name: string) => <Text strong>{name}</Text>,
    },
    {
      title: "Bank Type",
      dataIndex: "bank_type",
      key: "bank_type",
      render: (type: string) => <Tag color="blue">{type}</Tag>,
    },
    {
      title: "Supported Extensions",
      dataIndex: "supported_extensions",
      key: "supported_extensions",
      render: (extensions: string[]) => (
        <Space>
          {extensions.map((ext) => (
            <Tag key={ext}>{ext}</Tag>
          ))}
        </Space>
      ),
    },
    {
      title: "Description",
      dataIndex: "description",
      key: "description",
      ellipsis: true,
    },
  ];

  return (
    <div style={{ padding: "24px" }}>
      <Card>
        <Space direction="vertical" size="large" style={{ width: "100%" }}>
          <Title level={2}>
            <FileTextOutlined /> Available Parsers
          </Title>

          <Text>
            List of all available bank statement parsers. Each parser supports
            specific file formats and bank types.
          </Text>

          <Table
            columns={columns}
            dataSource={parsers}
            rowKey="name"
            loading={loading}
            pagination={{ pageSize: 10 }}
            onRow={(record) => ({
              onClick: () => setSelectedParser(record),
              style: { cursor: "pointer" },
            })}
          />

          {selectedParser && (
            <Card
              title={`Parser Details: ${selectedParser.name}`}
              extra={
                <Tag
                  color="blue"
                  onClick={() => setSelectedParser(null)}
                  style={{ cursor: "pointer" }}
                >
                  Close
                </Tag>
              }
            >
              <Descriptions column={1} bordered>
                <Descriptions.Item label="Name">
                  {selectedParser.name}
                </Descriptions.Item>
                <Descriptions.Item label="Bank Type">
                  <Tag color="blue">{selectedParser.bank_type}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Supported Extensions">
                  <Space>
                    {selectedParser.supported_extensions.map((ext) => (
                      <Tag key={ext}>{ext}</Tag>
                    ))}
                  </Space>
                </Descriptions.Item>
                <Descriptions.Item label="Description">
                  {selectedParser.description}
                </Descriptions.Item>
              </Descriptions>
            </Card>
          )}
        </Space>
      </Card>
    </div>
  );
};
