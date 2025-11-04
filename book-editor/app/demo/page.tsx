'use client';

import { useState, useEffect } from 'react';
import { Paragraph, ParagraphsResponse } from '@/types/paragraph';

export default function ParagraphsDemo() {
  const [paragraphs, setParagraphs] = useState<Paragraph[]>([]);
  const [loading, setLoading] = useState(false);
  const [cursor, setCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(true);
  const [total, setTotal] = useState<number | undefined>();
  const [limit, setLimit] = useState(10);

  const fetchParagraphs = async (reset = false) => {
    setLoading(true);
    try {
      const currentCursor = reset ? null : cursor;
      const url = currentCursor
        ? `/api/paragraphs?limit=${limit}&cursor=${currentCursor}`
        : `/api/paragraphs?limit=${limit}`;

      const response = await fetch(url);
      const data: ParagraphsResponse = await response.json();

      if (reset) {
        setParagraphs(data.data);
      } else {
        setParagraphs(prev => [...prev, ...data.data]);
      }

      setCursor(data.pagination.cursor);
      setHasMore(data.pagination.hasMore);
      if (data.pagination.total !== undefined) {
        setTotal(data.pagination.total);
      }
    } catch (error) {
      console.error('Error fetching paragraphs:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchParagraphs(true);
  }, []);

  const handleLoadMore = () => {
    if (!loading && hasMore) {
      fetchParagraphs(false);
    }
  };

  const handleReset = () => {
    setCursor(null);
    setHasMore(true);
    fetchParagraphs(true);
  };

  return (
    <div className="container mx-auto p-8">
      <h1 className="text-3xl font-bold mb-6">Paragraphs API Demo</h1>

      <div className="mb-6 flex gap-4 items-center">
        <div>
          <label className="block text-sm font-medium mb-2">
            Limit per page:
          </label>
          <select
            value={limit}
            onChange={(e) => {
              setLimit(Number(e.target.value));
              handleReset();
            }}
            className="border rounded px-3 py-2"
          >
            <option value={5}>5</option>
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
          </select>
        </div>

        {total !== undefined && (
          <div className="text-sm text-gray-600">
            Total paragraphs: <strong>{total}</strong>
          </div>
        )}

        <div className="text-sm text-gray-600">
          Loaded: <strong>{paragraphs.length}</strong>
        </div>
      </div>

      <div className="space-y-4">
        {paragraphs.map((paragraph, index) => (
          <div key={paragraph.id} className="border rounded-lg p-4 bg-white shadow">
            <div className="flex justify-between items-start mb-2">
              <div className="text-xs text-gray-500">
                #{index + 1} | ID: {paragraph.id}
              </div>
              {paragraph.order !== undefined && (
                <div className="text-xs text-gray-500">
                  Order: {paragraph.order}
                </div>
              )}
            </div>

            <p className="text-gray-800 mb-3">{paragraph.text}</p>

            <div className="grid grid-cols-2 gap-4 text-sm">
              {paragraph.previous && (
                <div className="border-l-2 border-blue-500 pl-3">
                  <div className="text-xs text-gray-500 mb-1">← Previous</div>
                  <div className="text-xs text-gray-700 line-clamp-2">
                    {paragraph.previous.text}
                  </div>
                </div>
              )}

              {paragraph.next && (
                <div className="border-l-2 border-green-500 pl-3">
                  <div className="text-xs text-gray-500 mb-1">Next →</div>
                  <div className="text-xs text-gray-700 line-clamp-2">
                    {paragraph.next.text}
                  </div>
                </div>
              )}
            </div>

            {(paragraph.section_id || paragraph.chapter_id) && (
              <div className="mt-3 text-xs text-gray-500 flex gap-4">
                {paragraph.chapter_id && (
                  <span>Chapter: {paragraph.chapter_id}</span>
                )}
                {paragraph.section_id && (
                  <span>Section: {paragraph.section_id}</span>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {hasMore && (
        <div className="mt-6 text-center">
          <button
            onClick={handleLoadMore}
            disabled={loading}
            className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {loading ? 'Loading...' : 'Load More'}
          </button>
        </div>
      )}

      {!hasMore && paragraphs.length > 0 && (
        <div className="mt-6 text-center text-gray-500">
          No more paragraphs to load
        </div>
      )}

      <div className="mt-8 p-4 bg-gray-100 rounded-lg">
        <h2 className="font-bold mb-2">API Info:</h2>
        <ul className="text-sm text-gray-700 space-y-1">
          <li>Current cursor: {cursor || 'null'}</li>
          <li>Has more: {hasMore ? 'Yes' : 'No'}</li>
          <li>Loading: {loading ? 'Yes' : 'No'}</li>
        </ul>
      </div>
    </div>
  );
}
