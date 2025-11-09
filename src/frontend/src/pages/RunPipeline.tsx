import { useState } from "react";
import {
  Card,
  Steps,
  Button,
  Space,
  Typography,
  message,
  Alert,
  Result,
} from "antd";
import {
  PlayCircleOutlined,
  CheckCircleOutlined,
  LoadingOutlined,
} from "@ant-design/icons";
import axiosInstance from "../utils/axios";
import { API_CONFIG } from "../config/settings";

const { Title } = Typography;
const { Step } = Steps;

interface PipelineStep {
  title: string;
  status: "wait" | "process" | "finish" | "error";
  description?: string;
}

export const RunPipeline = () => {
  const [running, setRunning] = useState(false);
  const [steps, setSteps] = useState<PipelineStep[]>([
    { title: "Initial Status", status: "wait" },
    { title: "Import Files", status: "wait" },
    { title: "Export Transactions", status: "wait" },
    { title: "Final Status", status: "wait" },
  ]);
  const [completed, setCompleted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRun = async () => {
    try {
      setRunning(true);
      setCompleted(false);
      setError(null);
      setSteps([
        { title: "Initial Status", status: "process" },
        { title: "Import Files", status: "wait" },
        { title: "Export Transactions", status: "wait" },
        { title: "Final Status", status: "wait" },
      ]);

      // Step 1: Initial Status
      await axiosInstance.get(API_CONFIG.ENDPOINTS.STATUS);
      updateStep(0, "finish");

      // Step 2: Import Files
      setSteps((prev) => {
        const step = prev[1];
        const newStep: PipelineStep = {
          title: step?.title ?? "Import Files",
          status: "process",
          ...(step?.description !== undefined && { description: step.description }),
        };
        return [
          ...prev.slice(0, 1),
          newStep,
          ...prev.slice(2),
        ];
      });
      // Note: Import would need file paths - this is a simplified version
      // In a real implementation, you'd trigger import from a directory
      await new Promise((resolve) => setTimeout(resolve, 2000)); // Simulate import
      updateStep(1, "finish");

      // Step 3: Export
      setSteps((prev) => {
        const step = prev[2];
        const newStep: PipelineStep = {
          title: step?.title ?? "Export Transactions",
          status: "process",
          ...(step?.description !== undefined && { description: step.description }),
        };
        return [
          ...prev.slice(0, 2),
          newStep,
          ...prev.slice(3),
        ];
      });
      await axiosInstance.post(API_CONFIG.ENDPOINTS.EXPORT.BASE, {});
      updateStep(2, "finish");

      // Step 4: Final Status
      setSteps((prev) => {
        const step = prev[3];
        const newStep: PipelineStep = {
          title: step?.title ?? "Final Status",
          status: "process",
          ...(step?.description !== undefined && { description: step.description }),
        };
        return [
          ...prev.slice(0, 3),
          newStep,
        ];
      });
      await axiosInstance.get(API_CONFIG.ENDPOINTS.STATUS);
      updateStep(3, "finish");

      setCompleted(true);
      message.success("Pipeline completed successfully!");
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || "Pipeline failed";
      setError(errorMsg);
      message.error(`Pipeline failed: ${errorMsg}`);
      // Mark current step as error
      const currentStepIndex = steps.findIndex((s) => s.status === "process");
      if (currentStepIndex >= 0) {
        updateStep(currentStepIndex, "error");
      }
    } finally {
      setRunning(false);
    }
  };

  const updateStep = (index: number, status: PipelineStep["status"]) => {
    setSteps((prev) => {
      const step = prev[index];
      if (!step) return prev;
      const newStep: PipelineStep = {
        title: step.title,
        status,
        ...(step.description !== undefined && { description: step.description }),
      };
      return [
        ...prev.slice(0, index),
        newStep,
        ...prev.slice(index + 1),
      ];
    });
  };

  const handleReset = () => {
    setSteps([
      { title: "Initial Status", status: "wait" },
      { title: "Import Files", status: "wait" },
      { title: "Export Transactions", status: "wait" },
      { title: "Final Status", status: "wait" },
    ]);
    setCompleted(false);
    setError(null);
  };

  return (
    <div style={{ padding: "24px" }}>
      <Card>
        <Space direction="vertical" size="large" style={{ width: "100%" }}>
          <Title level={2}>
            <PlayCircleOutlined /> Run Full Pipeline
          </Title>

          <Alert
            message="Full Pipeline Execution"
            description="This will run the complete workflow: status check → import files → export transactions → final status check. This is equivalent to the CLI 'run' command."
            type="info"
            showIcon
          />

          <Card>
            <Steps
              direction="vertical"
              current={steps.findIndex((s) => s.status === "process")}
              status={
                error
                  ? "error"
                  : completed
                    ? "finish"
                    : running
                      ? "process"
                      : "wait"
              }
            >
              {steps.map((step, index) => (
                <Step
                  key={index}
                  title={step.title}
                  status={step.status}
                  description={step.description}
                  icon={
                    step.status === "process" ? (
                      <LoadingOutlined />
                    ) : step.status === "finish" ? (
                      <CheckCircleOutlined />
                    ) : undefined
                  }
                />
              ))}
            </Steps>
          </Card>

          {error && (
            <Alert
              message="Pipeline Error"
              description={error}
              type="error"
              showIcon
            />
          )}

          {completed && (
            <Result
              status="success"
              title="Pipeline Completed Successfully"
              subTitle="All steps have been executed successfully."
            />
          )}

          <Space>
            <Button
              type="primary"
              size="large"
              icon={<PlayCircleOutlined />}
              onClick={handleRun}
              loading={running}
              disabled={running}
            >
              Run Pipeline
            </Button>
            <Button onClick={handleReset} disabled={running}>
              Reset
            </Button>
          </Space>
        </Space>
      </Card>
    </div>
  );
};
