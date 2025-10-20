'use client';

import { useState } from 'react';

export interface APIKey {
  id: string;
  name: string;
  key: string;
  maskedKey: string;
  createdAt: Date;
}

type SortOrder = 'asc' | 'desc';

interface APIKeysTableProps {
  apiKeys: APIKey[];
}

export default function APIKeysTable({ apiKeys }: APIKeysTableProps) {
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  const sortedKeys = [...apiKeys].sort((a, b) => {
    const comparison = b.createdAt.getTime() - a.createdAt.getTime();
    return sortOrder === 'desc' ? comparison : -comparison;
  });

  const toggleSortOrder = () => {
    setSortOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'));
  };

  const formatDate = (date: Date): string => {
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <TableHeader sortOrder={sortOrder} onToggleSort={toggleSortOrder} />
      
      {sortedKeys.length === 0 ? (
        <EmptyState />
      ) : (
        <TableBody apiKeys={sortedKeys} formatDate={formatDate} />
      )}
    </div>
  );
}

// Sub-component: Table Header
interface TableHeaderProps {
  sortOrder: SortOrder;
  onToggleSort: () => void;
}

function TableHeader({ sortOrder, onToggleSort }: TableHeaderProps) {
  return (
    <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
      <h3 className="text-lg font-semibold text-gray-900">
        Your API Keys
      </h3>
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-600">Sort by date:</span>
        <button
          onClick={onToggleSort}
          className="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-gray-700"
        >
          {sortOrder === 'desc' ? 'Newest First' : 'Oldest First'}
        </button>
      </div>
    </div>
  );
}

// Sub-component: Empty State
function EmptyState() {
  return (
    <div className="px-6 py-12 text-center">
      <p className="text-gray-500">
        No API keys yet. Generate your first key to get started!
      </p>
    </div>
  );
}

// Sub-component: Table Body
interface TableBodyProps {
  apiKeys: APIKey[];
  formatDate: (date: Date) => string;
}

function TableBody({ apiKeys, formatDate }: TableBodyProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
              Key Name
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
              API Key
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
              Date Created
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {apiKeys.map((apiKey) => (
            <TableRow 
              key={apiKey.id} 
              apiKey={apiKey} 
              formatDate={formatDate} 
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Sub-component: Table Row
interface TableRowProps {
  apiKey: APIKey;
  formatDate: (date: Date) => string;
}

function TableRow({ apiKey, formatDate }: TableRowProps) {
  return (
    <tr className="hover:bg-gray-50 transition-colors">
      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
        {apiKey.name}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 font-mono">
        {apiKey.maskedKey}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
        {formatDate(apiKey.createdAt)}
      </td>
    </tr>
  );
}