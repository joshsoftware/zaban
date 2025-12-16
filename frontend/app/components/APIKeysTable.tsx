"use client";

import { useState, useEffect } from "react";
import { fetchAPIKeys, deleteAPIKey, type APIKey } from "../lib/api-service";
import { Trash2 } from "lucide-react";

// Re-export APIKey type for use in other components
export type { APIKey };

type SortOrder = "asc" | "desc";

export default function APIKeysTable() {
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // Load API keys on mount
  useEffect(() => {
    loadAPIKeys();
  }, []);

  const loadAPIKeys = async () => {
    try {
      setLoading(true);
      setError(null);
      const keys = await fetchAPIKeys();
      setApiKeys(keys);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load API keys");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAPIKey = async (apiKeyId: string, keyName: string) => {
    const confirmDelete = window.confirm(
      `Are you sure you want to delete "${keyName}"? This action cannot be undone.`
    );

    if (!confirmDelete) return;

    try {
      setDeleting(apiKeyId);
      setDeleteError(null);
      await deleteAPIKey(apiKeyId);

      // Refetch the API keys list after successful deletion
      await loadAPIKeys();
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : "Failed to delete API key";
      setDeleteError(errorMsg);
      console.error("Delete error:", err);
    } finally {
      setDeleting(null);
    }
  };

  const sortedKeys = [...apiKeys].sort((a, b) => {
    const dateA = new Date(a.created_at).getTime();
    const dateB = new Date(b.created_at).getTime();
    const comparison = dateB - dateA;
    return sortOrder === "desc" ? comparison : -comparison;
  });

  const toggleSortOrder = () => {
    setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <TableHeader sortOrder={sortOrder} onToggleSort={toggleSortOrder} />

      {deleteError && <DeleteErrorAlert error={deleteError} />}

      {loading ? (
        <LoadingState />
      ) : error ? (
        <ErrorState error={error} />
      ) : sortedKeys.length === 0 ? (
        <EmptyState />
      ) : (
        <TableBody
          apiKeys={sortedKeys}
          formatDate={formatDate}
          onDelete={handleDeleteAPIKey}
          deleting={deleting}
        />
      )}
    </div>
  );
}

interface TableHeaderProps {
  sortOrder: SortOrder;
  onToggleSort: () => void;
}

function TableHeader({ sortOrder, onToggleSort }: TableHeaderProps) {
  return (
    <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
      <h3 className="text-lg font-semibold text-gray-900">Your API Keys</h3>
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-600">Sort by date:</span>
        <button
          onClick={onToggleSort}
          className="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-gray-700"
        >
          {sortOrder === "desc" ? "Newest First" : "Oldest First"}
        </button>
      </div>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="px-6 py-12 text-center">
      <p className="text-gray-500">Loading API keys...</p>
    </div>
  );
}

function ErrorState({ error }: { error: string }) {
  return (
    <div className="px-6 py-12 text-center">
      <p className="text-red-600 font-medium">{error}</p>
      <p className="text-gray-500 text-sm mt-2">
        Please check your authentication and try again.
      </p>
    </div>
  );
}

function DeleteErrorAlert({ error }: { error: string }) {
  return (
    <div className="px-6 py-3 bg-red-50 border-b border-red-200">
      <p className="text-red-700 text-sm">{error}</p>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="px-6 py-12 text-center">
      <p className="text-gray-500">
        No API keys yet. Generate your first key to get started!
      </p>
    </div>
  );
}

interface TableBodyProps {
  apiKeys: APIKey[];
  formatDate: (dateString: string) => string;
  onDelete: (id: string, name: string) => void;
  deleting: string | null;
}

function TableBody({
  apiKeys,
  formatDate,
  onDelete,
  deleting,
}: TableBodyProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
              Key Name
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
              Status
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
              Date Created
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
              Revoked Date
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {apiKeys.map((apiKey) => (
            <TableRow
              key={apiKey.id}
              apiKey={apiKey}
              formatDate={formatDate}
              onDelete={onDelete}
              isDeleting={deleting === apiKey.id}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}

interface TableRowProps {
  apiKey: APIKey;
  formatDate: (dateString: string) => string;
  onDelete: (id: string, name: string) => void;
  isDeleting: boolean;
}

function TableRow({ apiKey, formatDate, onDelete, isDeleting }: TableRowProps) {
  return (
    <tr className="hover:bg-gray-50 transition-colors">
      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
        {apiKey.name}
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <span
          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
            apiKey.is_active
              ? "bg-green-100 text-green-800"
              : "bg-red-100 text-red-800"
          }`}
        >
          {apiKey.is_active ? "Active" : "Inactive"}
        </span>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
        {formatDate(apiKey.created_at)}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
        {apiKey.revoked_at ? formatDate(apiKey.revoked_at) : "—"}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm">
        <button
          onClick={() => onDelete(apiKey.id, apiKey.name)}
          disabled={isDeleting}
          className="inline-flex items-center gap-2 px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Delete this API key"
        >
          {apiKey.is_active ? <Trash2 size={16} /> : ""}
        </button>
      </td>
    </tr>
  );
}
