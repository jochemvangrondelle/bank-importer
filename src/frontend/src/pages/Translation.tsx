import { useState, useEffect } from "react";
import {
  Card,
  Form,
  Input,
  Button,
  Space,
  message,
  Typography,
  Statistic,
  Row,
  Col,
  Table,
} from "antd";
import {
  TranslationOutlined,
  ClearOutlined,
  BarChartOutlined,
} from "@ant-design/icons";
import axiosInstance from "../utils/axios";
import { API_CONFIG } from "../config/settings";
import type { ColumnsType } from "antd/es/table";

const { Title } = Typography;

interface TranslationStats {
  total_cached: number;
  cache_file_size: number;
}

interface TranslationCache {
  source: string;
  target: string;
  source_language: string;
  target_language: string;
}

export const Translation = () => {
  const [form] = Form.useForm();
  const [stats, setStats] = useState<TranslationStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [cacheData, setCacheData] = useState<TranslationCache[]>([]);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const response = await axiosInstance.get(
        `${API_CONFIG.ENDPOINTS.TRANSLATION}/stats`
      );
      setStats(response.data);
    } catch (error: any) {
      // Stats might not be available
      console.error("Failed to load translation stats", error);
    }
  };

  const handleTranslate = async (values: { text: string }) => {
    try {
      setLoading(true);
      const response = await axiosInstance.post(
        `${API_CONFIG.ENDPOINTS.TRANSLATION}/translate`,
        { text: values.text }
      );
      message.success(`Translated: ${response.data.translated_text}`);
      form.setFieldsValue({ translated_text: response.data.translated_text });
      loadStats(); // Refresh stats
    } catch (error: any) {
      message.error("Failed to translate text");
    } finally {
      setLoading(false);
    }
  };

  const handleClearCache = async () => {
    try {
      await axiosInstance.delete(`${API_CONFIG.ENDPOINTS.TRANSLATION}/cache`);
      message.success("Translation cache cleared");
      setStats({ total_cached: 0, cache_file_size: 0 });
      setCacheData([]);
    } catch (error: any) {
      message.error("Failed to clear cache");
    }
  };

  const handleLoadCache = async () => {
    try {
      const response = await axiosInstance.get(
        `${API_CONFIG.ENDPOINTS.TRANSLATION}/cache`
      );
      setCacheData(response.data.cache || []);
    } catch (error: any) {
      message.error("Failed to load cache");
    }
  };

  const cacheColumns: ColumnsType<TranslationCache> = [
    {
      title: "Source Text",
      dataIndex: "source",
      key: "source",
      ellipsis: true,
    },
    {
      title: "Translated Text",
      dataIndex: "target",
      key: "target",
      ellipsis: true,
    },
    {
      title: "Source Language",
      dataIndex: "source_language",
      key: "source_language",
      width: 120,
    },
    {
      title: "Target Language",
      dataIndex: "target_language",
      key: "target_language",
      width: 120,
    },
  ];

  return (
    <div style={{ padding: "24px" }}>
      <Card>
        <Space direction="vertical" size="large" style={{ width: "100%" }}>
          <Title level={2}>
            <TranslationOutlined /> Translation Management
          </Title>

          <Card title="Statistics">
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="Cached Translations"
                  value={stats?.total_cached || 0}
                  prefix={<BarChartOutlined />}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="Cache File Size"
                  value={stats?.cache_file_size || 0}
                  suffix="bytes"
                />
              </Col>
            </Row>
          </Card>

          <Card title="Translate Text">
            <Form form={form} layout="vertical" onFinish={handleTranslate}>
              <Form.Item
                name="text"
                label="Text to Translate"
                rules={[
                  { required: true, message: "Please enter text to translate" },
                ]}
              >
                <Input.TextArea
                  rows={4}
                  placeholder="Enter text in Thai or other language to translate"
                />
              </Form.Item>
              <Form.Item name="translated_text" label="Translated Text">
                <Input.TextArea rows={4} readOnly />
              </Form.Item>
              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading}>
                  Translate
                </Button>
              </Form.Item>
            </Form>
          </Card>

          <Card
            title="Cache Management"
            extra={
              <Space>
                <Button onClick={handleLoadCache}>Load Cache</Button>
                <Button
                  danger
                  icon={<ClearOutlined />}
                  onClick={handleClearCache}
                >
                  Clear Cache
                </Button>
              </Space>
            }
          >
            <Table
              columns={cacheColumns}
              dataSource={cacheData}
              rowKey={(record, index) => `${record.source}-${index}`}
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </Space>
      </Card>
    </div>
  );
};
