import { useState, useEffect } from "react";
import {
  Steps,
  Card,
  Upload,
  Select,
  Form,
  Input,
  Button,
  Space,
  message,
  Row,
  Col,
  Table,
  Typography,
  Alert,
} from "antd";
import {
  UploadOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  DownloadOutlined,
} from "@ant-design/icons";
import type { UploadFile } from "antd";
import { API_CONFIG, EXPORT_CONFIG, UPLOAD_CONFIG } from "../config/settings";
import axiosInstance from "../utils/axios";
import { PDFViewer } from "../components/PDFViewer";
import type { ColumnsType } from "antd/es/table";

const { Step } = Steps;
const { Option } = Select;
const { Title, Text } = Typography;

interface Transaction {
  id?: number;
  date: string;
  description: string;
  translated_description?: string;
  amount: number;
  balance: number;
  transaction_type: string;
  currency: string;
  account_number: string;
}

interface ParseResponse {
  transactions: Transaction[];
  parser_name: string;
  total_transactions: number;
}

interface ParserInfo {
  name: string;
  bank_type: string;
  supported_extensions: string[];
  description: string;
}

export const ImportWizard = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [fileContent, setFileContent] = useState<string | null>(null);
  const [parsers, setParsers] = useState<ParserInfo[]>([]);
  const [selectedParser, setSelectedParser] = useState<string | null>(null);
  const [detectedParser, setDetectedParser] = useState<string | null>(null);
  const [password, setPassword] = useState<string>("");
  const [needsPassword, setNeedsPassword] = useState<boolean>(false);
  const [parsing, setParsing] = useState<boolean>(false);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [parseResult, setParseResult] = useState<ParseResponse | null>(null);
  const [form] = Form.useForm();

  // Load parsers on mount
  useEffect(() => {
    loadParsers();
  }, []);

  const loadParsers = async () => {
    try {
      const response = await axiosInstance.get(API_CONFIG.ENDPOINTS.PARSERS);
      setParsers(response.data.parsers || []);
    } catch (error) {
      message.error("Failed to load parsers");
    }
  };

  const handleFileUpload = async (file: File) => {
    // Read file for preview
    if (file.type === "application/pdf") {
      const reader = new FileReader();
      reader.onload = (e) => {
        const arrayBuffer = e.target?.result as ArrayBuffer;
        const blob = new Blob([arrayBuffer], { type: "application/pdf" });
        const url = URL.createObjectURL(blob);
        setFileContent(url);
      };
      reader.readAsArrayBuffer(file);
    } else {
      // For non-PDF files, show text preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setFileContent(e.target?.result as string);
      };
      reader.readAsText(file);
    }

    // Try to detect parser
    try {
      // For now, detect based on file extension
      const extension = file.name.split(".").pop()?.toLowerCase();
      const matchingParser = parsers.find((p) =>
        p.supported_extensions.includes(`.${extension}`)
      );
      if (matchingParser) {
        setDetectedParser(matchingParser.name);
        setSelectedParser(matchingParser.name);
        form.setFieldsValue({ parser_name: matchingParser.name });
      }
    } catch (error) {
      console.error("Parser detection failed:", error);
    }

    return false; // Prevent auto upload
  };

  const handleParse = async () => {
    if (!fileList[0]?.originFileObj) {
      message.error("Please select a file first");
      return;
    }

    setParsing(true);
    try {
      const formData = new FormData();
      formData.append("file", fileList[0].originFileObj);

      const formValues = form.getFieldsValue();
      if (formValues.parser_name) {
        formData.append("parser_name", formValues.parser_name);
      }
      if (formValues.account_number) {
        formData.append("account_number", formValues.account_number);
      }
      if (formValues.account_name) {
        formData.append("account_name", formValues.account_name);
      }
      if (formValues.bank_name) {
        formData.append("bank_name", formValues.bank_name);
      }
      if (formValues.currency) {
        formData.append("currency", formValues.currency);
      }
      if (formValues.country_code) {
        formData.append("country_code", formValues.country_code);
      }
      if (password) {
        formData.append("password", password);
      }
      formData.append(
        "parser_detection_behavior",
        formValues.parser_name ? "manual" : "automatic"
      );

      const response = await axiosInstance.post<ParseResponse>(
        API_CONFIG.ENDPOINTS.PARSE.FILE,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      setParseResult(response.data);
      setTransactions(response.data.transactions);
      setCurrentStep(2);
      message.success(
        `Successfully parsed ${response.data.total_transactions} transactions`
      );
    } catch (error: any) {
      if (error.response?.status === 400) {
        const errorMsg = error.response?.data?.detail || "Parsing failed";
        if (errorMsg.toLowerCase().includes("password")) {
          setNeedsPassword(true);
          message.warning("File requires a password");
        } else {
          message.error(errorMsg);
        }
      } else {
        message.error("Failed to parse file");
      }
    } finally {
      setParsing(false);
    }
  };

  const handleExport = async (targetName: "csv" | "yaml") => {
    if (!fileList[0]?.originFileObj || !parseResult) {
      message.error("Please parse a file first");
      return;
    }

    try {
      const formData = new FormData();
      formData.append("file", fileList[0].originFileObj);

      const formValues = form.getFieldsValue();
      if (formValues.parser_name) {
        formData.append("parser_name", formValues.parser_name);
      }
      if (formValues.account_number) {
        formData.append("account_number", formValues.account_number);
      }
      if (formValues.account_name) {
        formData.append("account_name", formValues.account_name);
      }
      if (formValues.bank_name) {
        formData.append("bank_name", formValues.bank_name);
      }
      if (formValues.currency) {
        formData.append("currency", formValues.currency);
      }
      if (formValues.country_code) {
        formData.append("country_code", formValues.country_code);
      }
      if (password) {
        formData.append("password", password);
      }
      formData.append("target_name", targetName);
      formData.append(
        "parser_detection_behavior",
        formValues.parser_name ? "manual" : "automatic"
      );

      const response = await axiosInstance.post(
        API_CONFIG.ENDPOINTS.PARSE.FILE_EXPORT,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
          responseType: "blob",
        }
      );

      // Create download link
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `transactions.${targetName}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      message.success(`Exported to ${targetName.toUpperCase()}`);
    } catch (error) {
      message.error("Failed to export file");
    }
  };

  const transactionColumns: ColumnsType<Transaction> = [
    {
      title: "Date",
      dataIndex: "date",
      key: "date",
      width: 120,
      render: (date: string) => new Date(date).toLocaleDateString(),
    },
    {
      title: "Description",
      dataIndex: "description",
      key: "description",
      ellipsis: true,
    },
    {
      title: "Translated",
      dataIndex: "translated_description",
      key: "translated_description",
      ellipsis: true,
    },
    {
      title: "Amount",
      dataIndex: "amount",
      key: "amount",
      width: 120,
      align: "right",
      render: (amount: number) => {
        const isCredit = amount >= 0;
        return (
          <Text style={{ color: isCredit ? "#52c41a" : "#ff4d4f" }}>
            {isCredit ? "+" : ""}
            {amount.toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </Text>
        );
      },
    },
    {
      title: "Balance",
      dataIndex: "balance",
      key: "balance",
      width: 120,
      align: "right",
      render: (balance: number) =>
        balance.toLocaleString(undefined, {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        }),
    },
    {
      title: "Type",
      dataIndex: "transaction_type",
      key: "transaction_type",
      width: 100,
    },
  ];

  const steps = [
    {
      title: "Prepare",
      icon: <FileTextOutlined />,
      content: (
        <Card>
          <Form form={form} layout="vertical">
            <Form.Item label="Select File" required>
              <Upload
                fileList={fileList}
                beforeUpload={handleFileUpload}
                onRemove={() => {
                  setFileList([]);
                  setFileContent(null);
                  setDetectedParser(null);
                  setSelectedParser(null);
                }}
                maxCount={1}
                accept={UPLOAD_CONFIG.ALLOWED_TYPES.join(",")}
              >
                <Button icon={<UploadOutlined />}>Select File</Button>
              </Upload>
            </Form.Item>

            {detectedParser && (
              <Alert
                message={`Detected parser: ${detectedParser}`}
                type="info"
                style={{ marginBottom: 16 }}
              />
            )}

            <Form.Item
              label="Parser"
              name="parser_name"
              tooltip="Leave empty for auto-detection"
            >
              <Select
                placeholder="Select parser or leave empty for auto-detection"
                value={selectedParser}
                onChange={(value) => {
                  setSelectedParser(value);
                  form.setFieldsValue({ parser_name: value });
                }}
                allowClear
              >
                {parsers.map((parser) => (
                  <Option key={parser.name} value={parser.name}>
                    {parser.name} - {parser.description}
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  label="Account Number"
                  name="account_number"
                  rules={[
                    {
                      required: true,
                      message: "Please enter account number",
                    },
                  ]}
                >
                  <Input placeholder="Account number" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  label="Account Name"
                  name="account_name"
                  rules={[
                    { required: true, message: "Please enter account name" },
                  ]}
                >
                  <Input placeholder="Account name" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  label="Bank Name"
                  name="bank_name"
                  rules={[
                    { required: true, message: "Please enter bank name" },
                  ]}
                >
                  <Input placeholder="Bank name" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="Currency" name="currency" initialValue="THB">
                  <Select>
                    <Option value="THB">THB</Option>
                    <Option value="USD">USD</Option>
                    <Option value="EUR">EUR</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Form.Item
              label="Country Code"
              name="country_code"
              initialValue="TH"
            >
              <Select>
                <Option value="TH">TH</Option>
                <Option value="US">US</Option>
                <Option value="GB">GB</Option>
              </Select>
            </Form.Item>
          </Form>

          <Space style={{ marginTop: 16 }}>
            <Button
              type="primary"
              onClick={() => {
                form.validateFields().then(() => {
                  if (fileList.length > 0) {
                    setCurrentStep(1);
                  } else {
                    message.error("Please select a file first");
                  }
                });
              }}
            >
              Next: Try Read
            </Button>
          </Space>
        </Card>
      ),
    },
    {
      title: "Try Read",
      icon: <CheckCircleOutlined />,
      content: (
        <Card>
          {needsPassword && (
            <Alert
              message="Password Required"
              description="This file requires a password to read."
              type="warning"
              style={{ marginBottom: 16 }}
            />
          )}

          <Form.Item label="Password (if required)">
            <Input.Password
              placeholder="Enter password for encrypted PDF"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </Form.Item>

          <Row gutter={16} style={{ marginTop: 24 }}>
            <Col span={12}>
              <Title level={5}>File Preview</Title>
              {fileContent &&
              fileList[0]?.originFileObj?.type === "application/pdf" ? (
                <PDFViewer fileUrl={fileContent} />
              ) : fileContent ? (
                <div
                  style={{
                    border: "1px solid #d9d9d9",
                    padding: 16,
                    maxHeight: 400,
                    overflow: "auto",
                    backgroundColor: "#fafafa",
                  }}
                >
                  <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>
                    {fileContent.substring(0, 1000)}
                    {fileContent.length > 1000 ? "..." : ""}
                  </pre>
                </div>
              ) : (
                <Text type="secondary">No file selected</Text>
              )}
            </Col>
            <Col span={12}>
              <Title level={5}>Parsed Transactions</Title>
              {transactions.length > 0 ? (
                <>
                  <Table
                    dataSource={transactions}
                    columns={transactionColumns}
                    rowKey={(record, index) =>
                      record.id?.toString() || (index ?? 0).toString()
                    }
                    pagination={{ pageSize: 10 }}
                    scroll={{ y: 400 }}
                    size="small"
                  />
                  <Space style={{ marginTop: 16 }}>
                    <Button
                      icon={<DownloadOutlined />}
                      onClick={() => handleExport(EXPORT_CONFIG.TARGETS.CSV)}
                    >
                      Export CSV
                    </Button>
                    <Button
                      icon={<DownloadOutlined />}
                      onClick={() => handleExport(EXPORT_CONFIG.TARGETS.YAML)}
                    >
                      Export YAML
                    </Button>
                  </Space>
                </>
              ) : (
                <div style={{ textAlign: "center", padding: 40 }}>
                  <Text type="secondary">
                    Click "Parse File" to extract transactions
                  </Text>
                  <br />
                  <Button
                    type="primary"
                    onClick={handleParse}
                    loading={parsing}
                    style={{ marginTop: 16 }}
                  >
                    Parse File
                  </Button>
                </div>
              )}
            </Col>
          </Row>

          <Space style={{ marginTop: 16 }}>
            <Button onClick={() => setCurrentStep(0)}>Back</Button>
            {transactions.length === 0 && (
              <Button type="primary" onClick={handleParse} loading={parsing}>
                Parse File
              </Button>
            )}
          </Space>
        </Card>
      ),
    },
  ];

  return (
    <div style={{ padding: "24px" }}>
      <Title level={2}>Import Wizard</Title>
      <Steps current={currentStep} style={{ marginBottom: 24 }}>
        {steps.map((step, index) => (
          <Step key={index} title={step.title} icon={step.icon} />
        ))}
      </Steps>
      {steps[currentStep]?.content}
    </div>
  );
};
