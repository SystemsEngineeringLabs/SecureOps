"use client";

import { useState, useRef, useEffect } from "react";
import { useAuth } from "@/hooks/useAuth";

export function Header() {
  const { user, logout } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <header className="flex h-16 items-center justify-between border-b border-base-200 bg-base-100 px-6">
      <div className="flex items-center gap-2 text-sm text-base-content/60">
        <span>Dashboard</span>
      </div>

      <div className="relative" ref={dropdownRef}>
        <button
          className="btn btn-ghost btn-sm gap-2"
          onClick={() => setDropdownOpen(!dropdownOpen)}
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-sm font-medium text-white">
            {user?.full_name?.charAt(0).toUpperCase() ?? "U"}
          </div>
          <span className="hidden text-sm sm:inline">{user?.full_name ?? "User"}</span>
          <svg
            className="h-4 w-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M6 9l6 6 6-6" />
          </svg>
        </button>

        {dropdownOpen && (
          <div className="absolute right-0 z-50 mt-2 w-48 rounded-lg border border-base-200 bg-base-100 py-1 shadow-lg">
            <a
              href="/admin/profile"
              className="block px-4 py-2 text-sm hover:bg-base-200"
            >
              Profile
            </a>
            <a
              href="/admin/settings"
              className="block px-4 py-2 text-sm hover:bg-base-200"
            >
              Settings
            </a>
            <div className="my-1 border-t border-base-200" />
            <button
              onClick={logout}
              className="block w-full px-4 py-2 text-left text-sm text-error hover:bg-base-200"
            >
              Logout
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
