import Link from "next/link";

export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-linear-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 font-sans">
      <main className="w-full max-w-4xl px-8 py-16">
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-12">
          <div className="mb-8">
            <h1 className="text-5xl font-bold text-gray-900 dark:text-white mb-4">
              Book Editor API
            </h1>
            <p className="text-xl text-gray-600 dark:text-gray-300">
              REST API для работы с параграфами книги Базиева из Neo4j базы данных
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-2 mb-10">
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6 border border-blue-200 dark:border-blue-800">
              <h2 className="text-xl font-semibold text-blue-900 dark:text-blue-100 mb-3">
                ✨ Возможности
              </h2>
              <ul className="space-y-2 text-gray-700 dark:text-gray-300">
                <li>• Получение параграфов с пагинацией</li>
                <li>• Связи previous & next</li>
                <li>• Cursor-based navigation</li>
                <li>• Фильтрация по главам и секциям</li>
                <li>• Виртуализация списков</li>
                <li>• Batch API для параграфов</li>
              </ul>
            </div>

            <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-6 border border-green-200 dark:border-green-800">
              <h2 className="text-xl font-semibold text-green-900 dark:text-green-100 mb-3">
                🚀 Endpoints
              </h2>
              <ul className="space-y-2 text-gray-700 dark:text-gray-300 font-mono text-sm">
                <li>GET /api/paragraphs</li>
                <li>GET /api/paragraphs/:id</li>
                <li>GET /api/paragraphs/meta</li>
                <li>POST /api/paragraphs/batch</li>
              </ul>
            </div>
          </div>

          <div className="flex flex-col gap-4 sm:flex-row">
            <Link
              href="/demo"
              className="flex h-14 items-center justify-center gap-2 rounded-lg bg-green-600 hover:bg-green-700 px-8 text-white font-semibold transition-colors shadow-lg"
            >
              📱 API Demo
            </Link>
            
            <a
              href="/API_DOCUMENTATION.md"
              target="_blank"
              rel="noopener noreferrer"
              className="flex h-14 items-center justify-center gap-2 rounded-lg border-2 border-gray-300 dark:border-gray-600 px-8 font-semibold transition-colors hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              📖 Документация API
            </a>
          </div>

          <div className="mt-10 p-6 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-3">
              Быстрый старт:
            </h3>
            <div className="bg-gray-900 dark:bg-black rounded p-4 overflow-x-auto">
              <code className="text-green-400 text-sm">
                curl http://localhost:3000/api/paragraphs?limit=10
              </code>
            </div>
          </div>

          <div className="mt-8 text-center text-sm text-gray-500 dark:text-gray-400">
            <p>Подключено к Neo4j • 69 иллюстраций • Полная навигация</p>
          </div>
        </div>
      </main>
    </div>
  );
}
