import { Refine } from "@refinedev/core";
import { RefineKbar, RefineKbarProvider } from "@refinedev/kbar";
import {
  ErrorComponent,
  ThemedLayoutV2,
  ThemedSiderV2,
  ThemedTitleV2,
  useNotificationProvider,
} from "@refinedev/antd";
import dataProvider from "@refinedev/simple-rest";
import routerProvider, {
  CatchAllNavigate,
  NavigateToResource,
  UnsavedChangesNotifier,
} from "@refinedev/react-router-v6";
import { App as AntdApp } from "antd";
import { Outlet, Route, Routes } from "react-router-dom";
import "@refinedev/antd/dist/reset.css";

import { Home } from "./pages/Home";
import { ImportWizard } from "./pages/ImportWizard";
import { Status } from "./pages/Status";
import { Configuration } from "./pages/Configuration";
import { Export } from "./pages/Export";
import { Transactions } from "./pages/Transactions";
import { Translation } from "./pages/Translation";
import { RunPipeline } from "./pages/RunPipeline";
import { Database } from "./pages/Database";
import { Parsers } from "./pages/Parsers";
import { API_CONFIG, APP_CONFIG } from "./config/settings";
import "./utils/axios";

function App() {
  return (
    <RefineKbarProvider>
      <AntdApp>
        <Refine
          dataProvider={dataProvider(API_CONFIG.BASE_URL)}
          routerProvider={routerProvider}
          notificationProvider={useNotificationProvider}
          resources={[
            {
              name: "home",
              list: "/home",
              meta: {
                label: "Home",
                icon: "🏠",
              },
            },
            {
              name: "import",
              list: "/import",
              meta: {
                label: "Import",
                icon: "📥",
              },
            },
            {
              name: "transactions",
              list: "/transactions",
              meta: {
                label: "Transactions",
                icon: "💳",
              },
            },
            {
              name: "export",
              list: "/export",
              meta: {
                label: "Export",
                icon: "📤",
              },
            },
            {
              name: "status",
              list: "/status",
              meta: {
                label: "Status",
                icon: "📊",
              },
            },
            {
              name: "configuration",
              list: "/configuration",
              meta: {
                label: "Configuration",
                icon: "⚙️",
              },
            },
            {
              name: "pipeline",
              list: "/pipeline",
              meta: {
                label: "Run Pipeline",
                icon: "🚀",
              },
            },
            {
              name: "translation",
              list: "/translation",
              meta: {
                label: "Translation",
                icon: "🌐",
              },
            },
            {
              name: "database",
              list: "/database",
              meta: {
                label: "Database",
                icon: "🗄️",
              },
            },
            {
              name: "parsers",
              list: "/parsers",
              meta: {
                label: "Parsers",
                icon: "📄",
              },
            },
          ]}
          options={{
            syncWithLocation: true,
            warnWhenUnsavedChanges: true,
            useNewQueryKeys: true,
          }}
        >
          <Routes>
            <Route
              element={
                <ThemedLayoutV2
                  Sider={() => <ThemedSiderV2 fixed />}
                  Title={({ collapsed }: { collapsed: boolean }) => (
                    <ThemedTitleV2
                      collapsed={collapsed}
                      text={APP_CONFIG.NAME}
                    />
                  )}
                >
                  <CatchAllNavigate to="/home" />
                  <Outlet />
                </ThemedLayoutV2>
              }
            >
              <Route index element={<NavigateToResource resource="home" />} />
              <Route path="/home" element={<Home />} />
              <Route path="/import" element={<ImportWizard />} />
              <Route path="/transactions" element={<Transactions />} />
              <Route path="/export" element={<Export />} />
              <Route path="/status" element={<Status />} />
              <Route path="/configuration" element={<Configuration />} />
              <Route path="/pipeline" element={<RunPipeline />} />
              <Route path="/translation" element={<Translation />} />
              <Route path="/database" element={<Database />} />
              <Route path="/parsers" element={<Parsers />} />
              <Route path="*" element={<ErrorComponent />} />
            </Route>
          </Routes>
          <RefineKbar />
          <UnsavedChangesNotifier />
        </Refine>
      </AntdApp>
    </RefineKbarProvider>
  );
}

export default App;
