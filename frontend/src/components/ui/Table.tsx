"use client";

import { clsx } from "clsx";

export interface ColumnDef<T> {
  header: string;
  accessor: keyof T | ((row: T) => unknown);
  render?: (value: unknown, row: T) => React.ReactNode;
  sortable?: boolean;
  className?: string;
}

interface TableProps<T> {
  columns: ColumnDef<T>[];
  data: T[];
  loading?: boolean;
  emptyMessage?: string;
  rowKey: (row: T) => string;
  className?: string;
}

function getCellValue<T>(row: T, accessor: ColumnDef<T>["accessor"]): unknown {
  if (typeof accessor === "function") return accessor(row);
  return row[accessor];
}

export function Table<T>({
  columns,
  data,
  loading = false,
  emptyMessage = "No data found",
  rowKey,
  className,
}: TableProps<T>) {
  if (loading) {
    return (
      <div className="overflow-x-auto">
        <table className={clsx("table", className)}>
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col.header}>{col.header}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: 5 }).map((_, i) => (
              <tr key={i}>
                {columns.map((col) => (
                  <td key={col.header}>
                    <div className="h-4 w-24 animate-pulse rounded bg-base-300" />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-gray-500">
        <p>{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className={clsx("table", className)}>
        <thead>
          <tr>
            {columns.map((col) => (
              <th
                key={col.header}
                className={clsx(
                  col.sortable && "cursor-pointer select-none",
                  col.className,
                )}
              >
                <span className="inline-flex items-center gap-1">
                  {col.header}
                  {col.sortable && (
                    <svg
                      className="h-3 w-3 opacity-40"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M7 15l5 5 5-5M7 9l5-5 5 5" />
                    </svg>
                  )}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr key={rowKey(row)} className="hover">
              {columns.map((col) => {
                const value = getCellValue(row, col.accessor);
                return (
                  <td key={col.header} className={col.className}>
                    {col.render ? col.render(value, row) : String(value ?? "")}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
