import { useState, useEffect } from "react";
import {
  Card,
  Table,
  Typography,
  Space,
  Input,
  Select,
  DatePicker,
  Button,
  Tag,
  message,
} from "antd";
import { SearchOutlined, ReloadOutlined } from "@ant-design/icons";
import axiosInstance from "../utils/axios";
import { API_CONFIG } from "../config/settings";
import type { ColumnsType } from "antd/es/table";
// Using native Date for now - can add dayjs if needed

const { Title } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;

interface Transaction {
  id: number;
  date: string;
  description: string;
  translated_description?: string;
  amount: number;
  balance: number;
  transaction_type: string;
  currency: string;
  account_number: string;
  account_name?: string;
  category?: string;
}

export const Transactions = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 50,
  });

  // Filters
  const [accountNumber, setAccountNumber] = useState<string>("");
  const [accountName, setAccountName] = useState<string>("");
  const [dateRange, setDateRange] = useState<[Date, Date] | null>(null);
  const [transactionType, setTransactionType] = useState<string | null>(null);
  const [category, setCategory] = useState<string | null>(null);

  useEffect(() => {
    loadTransactions();
  }, [pagination.current, pagination.pageSize]);

  const loadTransactions = async () => {
    try {
      setLoading(true);
      const params: any = {
        limit: pagination.pageSize,
        offset: (pagination.current - 1) * pagination.pageSize,
      };

      if (accountNumber) params.account_number = accountNumber;
      if (accountName) params.account_name = accountName;
      if (dateRange && dateRange[0] && dateRange[1]) {
        params.date_from = dateRange[0].toISOString();
        params.date_to = dateRange[1].toISOString();
      }
      if (transactionType) params.transaction_type = transactionType;
      if (category) params.category = category;

      const response = await axiosInstance.get(
        API_CONFIG.ENDPOINTS.TRANSACTIONS,
        {
          params,
        }
      );
      setTransactions(response.data.transactions || []);
      setTotal(response.data.total || 0);
    } catch (error: any) {
      message.error("Failed to load transactions");
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setPagination({ ...pagination, current: 1 });
    loadTransactions();
  };

  const handleReset = () => {
    setAccountNumber("");
    setAccountName("");
    setDateRange(null);
    setTransactionType("");
    setCategory("");
    setPagination({ ...pagination, current: 1 });
    setTimeout(() => loadTransactions(), 100);
  };

  const columns: ColumnsType<Transaction> = [
    {
      title: "Date",
      dataIndex: "date",
      key: "date",
      width: 120,
      render: (date: string) => new Date(date).toLocaleDateString(),
      sorter: true,
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
      render: (text: string | undefined) => text || "-",
    },
    {
      title: "Amount",
      dataIndex: "amount",
      key: "amount",
      width: 120,
      render: (amount: number, record: Transaction) => (
        <span style={{ color: amount >= 0 ? "green" : "red" }}>
          {amount >= 0 ? "+" : ""}
          {amount.toLocaleString()} {record.currency}
        </span>
      ),
      sorter: true,
    },
    {
      title: "Balance",
      dataIndex: "balance",
      key: "balance",
      width: 120,
      render: (balance: number, record: Transaction) =>
        `${balance.toLocaleString()} ${record.currency}`,
      sorter: true,
    },
    {
      title: "Type",
      dataIndex: "transaction_type",
      key: "transaction_type",
      width: 100,
      render: (type: string) => <Tag>{type}</Tag>,
    },
    {
      title: "Account",
      dataIndex: "account_number",
      key: "account_number",
      width: 150,
      render: (accountNumber: string, record: Transaction) =>
        record.account_name
          ? `${record.account_name} (${accountNumber})`
          : accountNumber,
    },
    {
      title: "Category",
      dataIndex: "category",
      key: "category",
      width: 120,
      render: (category: string | undefined) =>
        category ? <Tag color="blue">{category}</Tag> : "-",
    },
  ];

  return (
    <div style={{ padding: "24px" }}>
      <Card>
        <Space direction="vertical" size="large" style={{ width: "100%" }}>
          <Title level={2}>Transactions</Title>

          <Card>
            <Space direction="vertical" size="middle" style={{ width: "100%" }}>
              <Space wrap>
                <Input
                  placeholder="Account Number"
                  value={accountNumber}
                  onChange={(e) => setAccountNumber(e.target.value)}
                  style={{ width: 200 }}
                />
                <Input
                  placeholder="Account Name"
                  value={accountName}
                  onChange={(e) => setAccountName(e.target.value)}
                  style={{ width: 200 }}
                />
                <RangePicker
                  onChange={(dates) =>
                    setDateRange(
                      dates
                        ? [
                            dates[0]?.toDate() as Date,
                            dates[1]?.toDate() as Date,
                          ]
                        : null
                    )
                  }
                />
                <Select
                  placeholder="Transaction Type"
                  value={transactionType}
                  onChange={setTransactionType}
                  allowClear
                  style={{ width: 150 }}
                >
                  <Option value="credit">Credit</Option>
                  <Option value="debit">Debit</Option>
                </Select>
                <Select
                  placeholder="Category"
                  value={category}
                  onChange={setCategory}
                  allowClear
                  style={{ width: 150 }}
                >
                  {/* Categories would come from API */}
                </Select>
                <Button
                  type="primary"
                  icon={<SearchOutlined />}
                  onClick={handleSearch}
                >
                  Search
                </Button>
                <Button icon={<ReloadOutlined />} onClick={handleReset}>
                  Reset
                </Button>
              </Space>
            </Space>
          </Card>

          <Card>
            <Table
              columns={columns}
              dataSource={transactions}
              rowKey="id"
              loading={loading}
              pagination={{
                current: pagination.current,
                pageSize: pagination.pageSize,
                total: total,
                showSizeChanger: true,
                showTotal: (total) => `Total ${total} transactions`,
                onChange: (page, pageSize) => {
                  setPagination({ current: page, pageSize });
                },
              }}
              scroll={{ x: 1200 }}
            />
          </Card>
        </Space>
      </Card>
    </div>
  );
};
