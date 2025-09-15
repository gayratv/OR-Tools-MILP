import globals from 'globals';
import tseslint from 'typescript-eslint';
import eslint from '@eslint/js';

export default tseslint.config(
  // Глобальные переменные для среды выполнения (Node.js)
  {
    languageOptions: {
      globals: {
        ...globals.node,
      },
    },
  },

  // Базовые правила ESLint
  eslint.configs.recommended,

  // Правила для TypeScript
  // Эта конфигурация автоматически найдет tsconfig.json и применит правила
  ...tseslint.configs.recommended,
);