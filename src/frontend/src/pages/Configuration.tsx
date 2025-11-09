import { useState, useEffect } from "react";
import {
  Card,
  Tabs,
  Form,
  Input,
  Button,
  Space,
  message,
  Table,
  Typography,
  Switch,
  Select,
  Modal,
  Popconfirm,
} from "antd";
import {
  SettingOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
} from "@ant-design/icons";
import axiosInstance from "../utils/axios";
import { API_CONFIG } from "../config/settings";
import type { ColumnsType } from "antd/es/table";

const { Title } = Typography;
const { Option } = Select;

interface Account {
  name: string;
  account_number: string;
  bank_name: string;
  parser_name: string;
  currency?: string;
  country_code?: string;
}

interface Target {
  name: string;
  type: string;
  enabled: boolean;
  path?: string;
  format?: string;
}

interface ConfigData {
  accounts: Account[];
  targets: Target[];
  settings: {
    database_url?: string;
    output_dir?: string;
    timezone?: string;
  };
}

export const Configuration = () => {
  const [config, setConfig] = useState<ConfigData | null>(null);
  const [loading, setLoading] = useState(true);
  const [accountForm] = Form.useForm();
  const [targetForm] = Form.useForm();
  const [settingsForm] = Form.useForm();
  const [accountModalVisible, setAccountModalVisible] = useState(false);
  const [targetModalVisible, setTargetModalVisible] = useState(false);
  const [editingAccount, setEditingAccount] = useState<Account | null>(null);
  const [editingTarget, setEditingTarget] = useState<Target | null>(null);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      setLoading(true);
      const response = await axiosInstance.get(API_CONFIG.ENDPOINTS.CONFIG.BASE);
      setConfig(response.data);
      if (response.data.settings) {
        settingsForm.setFieldsValue(response.data.settings);
      }
    } catch (error: any) {
      message.error("Failed to load configuration");
    } finally {
      setLoading(false);
    }
  };

  const handleSaveSettings = async (values: any) => {
    try {
      await axiosInstance.put(API_CONFIG.ENDPOINTS.CONFIG.BASE, {
        settings: values,
      });
      message.success("Settings saved successfully");
      loadConfig();
    } catch (error: any) {
      message.error("Failed to save settings");
    }
  };

  const handleAddAccount = () => {
    setEditingAccount(null);
    accountForm.resetFields();
    setAccountModalVisible(true);
  };

  const handleEditAccount = (account: Account) => {
    setEditingAccount(account);
    accountForm.setFieldsValue(account);
    setAccountModalVisible(true);
  };

  const handleDeleteAccount = async (accountName: string) => {
    try {
      // Get current accounts and remove the one to delete
      const currentAccounts = config?.accounts || [];
      const updatedAccounts = currentAccounts.filter(
        (acc) => acc.name !== accountName
      );
      await axiosInstance.put(API_CONFIG.ENDPOINTS.CONFIG.BASE, {
        accounts: updatedAccounts,
      });
      message.success("Account deleted successfully");
      loadConfig();
    } catch (error: any) {
      message.error("Failed to delete account");
    }
  };

  const handleSaveAccount = async (values: Account) => {
    try {
      const currentAccounts = config?.accounts || [];
      let updatedAccounts: Account[];

      if (editingAccount) {
        // Update existing account
        updatedAccounts = currentAccounts.map((acc) =>
          acc.name === editingAccount.name ? { ...values, name: values.name } : acc
        );
      } else {
        // Add new account
        updatedAccounts = [...currentAccounts, values];
      }

      await axiosInstance.put(API_CONFIG.ENDPOINTS.CONFIG.BASE, {
        accounts: updatedAccounts,
      });
      message.success(
        editingAccount ? "Account updated successfully" : "Account added successfully"
      );
      setAccountModalVisible(false);
      loadConfig();
    } catch (error: any) {
      message.error("Failed to save account");
    }
  };

  const handleAddTarget = () => {
    setEditingTarget(null);
    targetForm.resetFields();
    setTargetModalVisible(true);
  };

  const handleEditTarget = (target: Target) => {
    setEditingTarget(target);
    targetForm.setFieldsValue(target);
    setTargetModalVisible(true);
  };

  const handleDeleteTarget = async (targetName: string) => {
    try {
      const currentTargets = config?.targets || [];
      const updatedTargets = currentTargets.filter(
        (tgt) => tgt.name !== targetName
      );
      await axiosInstance.put(API_CONFIG.ENDPOINTS.CONFIG.BASE, {
        targets: updatedTargets,
      });
      message.success("Target deleted successfully");
      loadConfig();
    } catch (error: any) {
      message.error("Failed to delete target");
    }
  };

  const handleSaveTarget = async (values: Target) => {
    try {
      const currentTargets = config?.targets || [];
      let updatedTargets: Target[];

      if (editingTarget) {
        updatedTargets = currentTargets.map((tgt) =>
          tgt.name === editingTarget.name ? { ...values, name: values.name } : tgt
        );
      } else {
        updatedTargets = [...currentTargets, values];
      }

      await axiosInstance.put(API_CONFIG.ENDPOINTS.CONFIG.BASE, {
        targets: updatedTargets,
      });
      message.success(
        editingTarget ? "Target updated successfully" : "Target added successfully"
      );
      setTargetModalVisible(false);
      loadConfig();
    } catch (error: any) {
      message.error("Failed to save target");
    }
  };

  const accountColumns: ColumnsType<Account> = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
    },
    {
      title: "Account Number",
      dataIndex: "account_number",
      key: "account_number",
    },
    {
      title: "Bank Name",
      dataIndex: "bank_name",
      key: "bank_name",
    },
    {
      title: "Parser",
      dataIndex: "parser_name",
      key: "parser_name",
    },
    {
      title: "Currency",
      dataIndex: "currency",
      key: "currency",
    },
    {
      title: "Actions",
      key: "actions",
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEditAccount(record)}
          >
            Edit
          </Button>
          <Popconfirm
            title="Delete account"
            description="Are you sure you want to delete this account?"
            onConfirm={() => handleDeleteAccount(record.name)}
            okText="Yes"
            cancelText="No"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              Delete
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const targetColumns: ColumnsType<Target> = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
    },
    {
      title: "Type",
      dataIndex: "type",
      key: "type",
    },
    {
      title: "Enabled",
      dataIndex: "enabled",
      key: "enabled",
      render: (enabled: boolean) => (enabled ? "Yes" : "No"),
    },
    {
      title: "Path",
      dataIndex: "path",
      key: "path",
    },
    {
      title: "Format",
      dataIndex: "format",
      key: "format",
    },
    {
      title: "Actions",
      key: "actions",
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEditTarget(record)}
          >
            Edit
          </Button>
          <Popconfirm
            title="Delete target"
            description="Are you sure you want to delete this target?"
            onConfirm={() => handleDeleteTarget(record.name)}
            okText="Yes"
            cancelText="No"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              Delete
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: "24px" }}>
      <Card>
        <Space direction="vertical" size="large" style={{ width: "100%" }}>
          <Title level={2}>
            <SettingOutlined /> Configuration
          </Title>

          <Tabs
            defaultActiveKey="settings"
            items={[
              {
                key: "settings",
                label: "Settings",
                children: (
                  <Card>
                    <Form
                      form={settingsForm}
                      layout="vertical"
                      onFinish={handleSaveSettings}
                    >
                      <Form.Item
                        name="database_url"
                        label="Database URL"
                        tooltip="SQLite database file path"
                      >
                        <Input placeholder="sqlite:///bank_importer.db" />
                      </Form.Item>
                      <Form.Item
                        name="output_dir"
                        label="Output Directory"
                        tooltip="Directory for exported files"
                      >
                        <Input placeholder="data/out" />
                      </Form.Item>
                      <Form.Item
                        name="timezone"
                        label="Timezone"
                        tooltip="Timezone for date/time operations"
                      >
                        <Input placeholder="Asia/Bangkok" />
                      </Form.Item>
                      <Form.Item>
                        <Button type="primary" htmlType="submit">
                          Save Settings
                        </Button>
                      </Form.Item>
                    </Form>
                  </Card>
                ),
              },
              {
                key: "accounts",
                label: "Accounts",
                children: (
                  <Card
                    title="Bank Accounts"
                    extra={
                      <Button
                        type="primary"
                        icon={<PlusOutlined />}
                        onClick={handleAddAccount}
                      >
                        Add Account
                      </Button>
                    }
                  >
                    <Table
                      columns={accountColumns}
                      dataSource={config?.accounts || []}
                      rowKey="name"
                      loading={loading}
                    />
                  </Card>
                ),
              },
              {
                key: "targets",
                label: "Export Targets",
                children: (
                  <Card
                    title="Export Targets"
                    extra={
                      <Button
                        type="primary"
                        icon={<PlusOutlined />}
                        onClick={handleAddTarget}
                      >
                        Add Target
                      </Button>
                    }
                  >
                    <Table
                      columns={targetColumns}
                      dataSource={config?.targets || []}
                      rowKey="name"
                      loading={loading}
                    />
                  </Card>
                ),
              },
            ]}
          />
        </Space>
      </Card>

      {/* Account Modal */}
      <Modal
        title={editingAccount ? "Edit Account" : "Add Account"}
        open={accountModalVisible}
        onCancel={() => setAccountModalVisible(false)}
        footer={null}
      >
        <Form form={accountForm} layout="vertical" onFinish={handleSaveAccount}>
          <Form.Item
            name="name"
            label="Account Name"
            rules={[{ required: true, message: "Please enter account name" }]}
          >
            <Input placeholder="krungsri_pdf" />
          </Form.Item>
          <Form.Item
            name="account_number"
            label="Account Number"
            rules={[{ required: true, message: "Please enter account number" }]}
          >
            <Input placeholder="1234567890" />
          </Form.Item>
          <Form.Item
            name="bank_name"
            label="Bank Name"
            rules={[{ required: true, message: "Please enter bank name" }]}
          >
            <Input placeholder="Krungsri" />
          </Form.Item>
          <Form.Item
            name="parser_name"
            label="Parser Name"
            rules={[{ required: true, message: "Please select parser" }]}
          >
            <Input placeholder="krungsri_pdf" />
          </Form.Item>
          <Form.Item name="currency" label="Currency">
            <Select defaultValue="THB">
              <Option value="THB">THB</Option>
              <Option value="USD">USD</Option>
              <Option value="EUR">EUR</Option>
            </Select>
          </Form.Item>
          <Form.Item name="country_code" label="Country Code">
            <Select defaultValue="TH">
              <Option value="TH">TH</Option>
              <Option value="US">US</Option>
              <Option value="GB">GB</Option>
            </Select>
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {editingAccount ? "Update" : "Add"}
              </Button>
              <Button onClick={() => setAccountModalVisible(false)}>Cancel</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Target Modal */}
      <Modal
        title={editingTarget ? "Edit Target" : "Add Target"}
        open={targetModalVisible}
        onCancel={() => setTargetModalVisible(false)}
        footer={null}
      >
        <Form form={targetForm} layout="vertical" onFinish={handleSaveTarget}>
          <Form.Item
            name="name"
            label="Target Name"
            rules={[{ required: true, message: "Please enter target name" }]}
          >
            <Input placeholder="csv_export" />
          </Form.Item>
          <Form.Item
            name="type"
            label="Type"
            rules={[{ required: true, message: "Please select type" }]}
          >
            <Select>
              <Option value="file">File</Option>
              <Option value="directory">Directory</Option>
            </Select>
          </Form.Item>
          <Form.Item name="enabled" label="Enabled" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="path" label="Path">
            <Input placeholder="data/out/export.csv" />
          </Form.Item>
          <Form.Item name="format" label="Format">
            <Select>
              <Option value="csv">CSV</Option>
              <Option value="yaml">YAML</Option>
            </Select>
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {editingTarget ? "Update" : "Add"}
              </Button>
              <Button onClick={() => setTargetModalVisible(false)}>Cancel</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};
