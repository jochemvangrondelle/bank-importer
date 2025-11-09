module.exports = {
  root: true,
  env: { browser: true, es2020: true, node: true },
  extends: [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:@typescript-eslint/recommended-type-checked",
    "plugin:@typescript-eslint/strict-type-checked",
    "plugin:react-hooks/recommended",
    "plugin:react/jsx-runtime",
    "plugin:security/recommended",
    "plugin:sonarjs/recommended",
  ],
  ignorePatterns: ["dist", ".eslintrc.cjs", "src/api/generated", "*.config.*"],
  parser: "@typescript-eslint/parser",
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module",
    project: ["./tsconfig.json", "./tsconfig.node.json"],
    tsconfigRootDir: __dirname,
  },
  plugins: [
    "react-refresh",
    "react",
    "security",
    "sonarjs",
    "import",
    "unicorn",
    "no-secrets",
  ],
  settings: {
    react: {
      version: "detect",
    },
  },
  rules: {
    // React Refresh
    "react-refresh/only-export-components": [
      "warn",
      { allowConstantExport: true },
    ],

    // TypeScript strict rules
    "@typescript-eslint/no-explicit-any": "error",
    "@typescript-eslint/no-unsafe-assignment": "error",
    "@typescript-eslint/no-unsafe-member-access": "error",
    "@typescript-eslint/no-unsafe-call": "error",
    "@typescript-eslint/no-unsafe-return": "error",
    "@typescript-eslint/no-unsafe-argument": "error",
    "@typescript-eslint/explicit-function-return-type": [
      "warn",
      {
        allowExpressions: true,
        allowTypedFunctionExpressions: true,
        allowHigherOrderFunctions: true,
      },
    ],
    "@typescript-eslint/no-unused-vars": [
      "error",
      {
        argsIgnorePattern: "^_",
        varsIgnorePattern: "^_",
        caughtErrorsIgnorePattern: "^_",
      },
    ],
    "@typescript-eslint/consistent-type-definitions": ["error", "interface"],
    "@typescript-eslint/consistent-type-imports": [
      "error",
      { prefer: "type-imports", fixStyle: "inline-type-imports" },
    ],
    "@typescript-eslint/no-misused-promises": [
      "error",
      {
        checksVoidReturn: false,
      },
    ],
    "@typescript-eslint/await-thenable": "error",
    "@typescript-eslint/no-floating-promises": "error",
    "@typescript-eslint/no-unnecessary-type-assertion": "error",
    "@typescript-eslint/prefer-nullish-coalescing": "error",
    "@typescript-eslint/prefer-optional-chain": "error",
    "@typescript-eslint/restrict-template-expressions": [
      "error",
      {
        allowNumber: true,
        allowBoolean: true,
      },
    ],

    // General code quality
    "no-console": ["warn", { allow: ["warn", "error"] }],
    "no-debugger": "error",
    "no-alert": "error",
    "no-eval": "error",
    "no-implied-eval": "error",
    "no-new-func": "error",
    "no-script-url": "error",
    "no-void": "error",
    "prefer-const": "error",
    "no-var": "error",
    "object-shorthand": "error",
    "prefer-arrow-callback": "error",
    "prefer-template": "error",
    "prefer-destructuring": ["error", { object: true, array: false }],
    "no-nested-ternary": "warn",
    "no-param-reassign": ["error", { props: true }],
    "no-plusplus": ["error", { allowForLoopAfterthoughts: true }],
    "no-unused-expressions": "error",
    "no-useless-concat": "error",
    "no-useless-return": "error",
    "prefer-promise-reject-errors": "error",
    "require-await": "error",
    "yoda": "error",

    // Import/export rules
    "import/order": [
      "error",
      {
        groups: [
          "builtin",
          "external",
          "internal",
          "parent",
          "sibling",
          "index",
        ],
        "newlines-between": "always",
        alphabetize: {
          order: "asc",
          caseInsensitive: true,
        },
      },
    ],
    "import/no-duplicates": "error",
    "import/no-unresolved": "off", // TypeScript handles this
    "import/no-cycle": ["error", { maxDepth: 3 }],
    "import/no-self-import": "error",
    "import/no-useless-path-segments": "error",

    // React rules
    "react/jsx-boolean-value": ["error", "never"],
    "react/jsx-curly-brace-presence": [
      "error",
      { props: "never", children: "never" },
    ],
    "react/jsx-fragments": ["error", "syntax"],
    "react/jsx-no-useless-fragment": "error",
    "react/jsx-pascal-case": "error",
    "react/no-array-index-key": "warn",
    "react/no-danger": "error",
    "react/no-deprecated": "error",
    "react/no-direct-mutation-state": "error",
    "react/no-unescaped-entities": "error",
    "react/no-unused-state": "error",
    "react/prefer-es6-class": "error",
    "react/self-closing-comp": "error",
    "react/jsx-key": "error",
    "react-hooks/rules-of-hooks": "error",
    "react-hooks/exhaustive-deps": "warn",

    // Security rules
    "security/detect-object-injection": "warn",
    "security/detect-non-literal-fs-filename": "warn",
    "security/detect-eval-with-expression": "error",
    "security/detect-no-csrf-before-method-override": "error",
    "security/detect-possible-timing-attacks": "warn",
    "no-secrets/no-secrets": [
      "error",
      {
        tolerance: 4.2,
        ignoreContent: ["password", "secret", "key", "token"],
      },
    ],

    // SonarJS rules (code quality and duplication)
    "sonarjs/cognitive-complexity": ["error", 15],
    "sonarjs/no-duplicate-string": ["error", 3],
    "sonarjs/no-identical-expressions": "error",
    "sonarjs/no-small-switch": "error",
    "sonarjs/prefer-immediate-return": "error",
    "sonarjs/prefer-object-literal": "error",
    "sonarjs/prefer-single-boolean-return": "error",
    "sonarjs/no-redundant-boolean": "error",
    "sonarjs/no-redundant-jump": "error",
    "sonarjs/prefer-while": "error",

    // Unicorn rules (best practices)
    "unicorn/better-regex": "error",
    "unicorn/catch-error-name": "error",
    "unicorn/consistent-destructuring": "error",
    "unicorn/consistent-function-scoping": "error",
    "unicorn/explicit-length-check": "error",
    "unicorn/filename-case": [
      "error",
      {
        case: "kebabCase",
        ignore: [/^[A-Z]/, /\.config\./],
      },
    ],
    "unicorn/no-array-callback-reference": "error",
    "unicorn/no-array-for-each": "error",
    "unicorn/no-array-push-push": "error",
    "unicorn/no-console-spaces": "error",
    "unicorn/no-for-loop": "error",
    "unicorn/no-lonely-if": "error",
    "unicorn/no-nested-ternary": "error",
    "unicorn/no-new-buffer": "error",
    "unicorn/no-unreadable-array-destructuring": "error",
    "unicorn/no-useless-undefined": "error",
    "unicorn/prefer-array-find": "error",
    "unicorn/prefer-array-index-of": "error",
    "unicorn/prefer-array-some": "error",
    "unicorn/prefer-date-now": "error",
    "unicorn/prefer-includes": "error",
    "unicorn/prefer-module": "off", // Not applicable for Vite
    "unicorn/prefer-node-protocol": "error",
    "unicorn/prefer-number-properties": "error",
    "unicorn/prefer-optional-catch-binding": "error",
    "unicorn/prefer-regexp-test": "error",
    "unicorn/prefer-set-has": "error",
    "unicorn/prefer-spread": "error",
    "unicorn/prefer-string-starts-ends-with": "error",
    "unicorn/prefer-string-trim-start-end": "error",
    "unicorn/prefer-top-level-await": "off", // Not always applicable
    "unicorn/require-array-join-separator": "error",
    "unicorn/require-number-to-fixed-digits-argument": "error",
  },
};
