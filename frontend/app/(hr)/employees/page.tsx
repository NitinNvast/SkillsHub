"use client";

import { useState, useRef } from "react";
import Link from "next/link";
import { Search, MapPin, Briefcase, UserPlus, Upload, FileText, X, CheckCircle, AlertCircle } from "lucide-react";
import * as Dialog from "@radix-ui/react-dialog";
import { toast } from "sonner";
import { useEmployees, useCreateEmployee, useBulkUpload, useCsvImport, type BulkUploadResult } from "@/lib/api/hooks";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { cn } from "@/lib/utils";
import { ApiError } from "@/lib/api/client";

const AVAILABILITY_STYLE: Record<string, string> = {
  available: "bg-emerald-50 text-emerald-700 border-emerald-200",
  partial:   "bg-amber-50 text-amber-700 border-amber-200",
  allocated: "bg-slate-100 text-slate-600 border-slate-200",
};

const AVAILABILITY_LABEL: Record<string, string> = {
  available: "Available",
  partial:   "Partial",
  allocated: "Allocated",
};

type BulkTab = "pdf" | "csv";

function BulkResultsTable({ results }: { results: BulkUploadResult[] }) {
  return (
    <div className="mt-4 space-y-1.5 max-h-52 overflow-y-auto">
      {results.map((r, i) => (
        <div key={i} className="flex items-start gap-2 text-xs rounded-lg border border-[var(--color-border)] px-3 py-2">
          {r.status === "queued" ? (
            <CheckCircle className="h-3.5 w-3.5 text-emerald-500 shrink-0 mt-0.5" />
          ) : (
            <AlertCircle className="h-3.5 w-3.5 text-red-500 shrink-0 mt-0.5" />
          )}
          <div className="min-w-0">
            <p className="font-medium truncate">{r.filename}</p>
            {r.error && <p className="text-red-600 mt-0.5">{r.error}</p>}
          </div>
          <span className={cn("ml-auto shrink-0 font-semibold", r.status === "queued" ? "text-emerald-600" : "text-red-600")}>
            {r.status === "queued" ? "✓" : "✗"}
          </span>
        </div>
      ))}
    </div>
  );
}

export default function EmployeesPage() {
  const [q, setQ] = useState("");
  const { data: employees, isLoading } = useEmployees(q || undefined);

  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [title, setTitle] = useState("");
  const [location, setLocation] = useState("");
  const [formError, setFormError] = useState("");

  // Bulk import state
  const [bulkOpen, setBulkOpen] = useState(false);
  const [bulkTab, setBulkTab] = useState<BulkTab>("pdf");
  const [pdfFiles, setPdfFiles] = useState<File[]>([]);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [bulkResults, setBulkResults] = useState<BulkUploadResult[] | null>(null);
  const pdfInputRef = useRef<HTMLInputElement>(null);
  const csvInputRef = useRef<HTMLInputElement>(null);

  const { mutate: createEmployee, isPending: isCreating } = useCreateEmployee();
  const { mutate: bulkUpload, isPending: isBulkUploading } = useBulkUpload();
  const { mutate: csvImport, isPending: isCsvImporting } = useCsvImport();

  function resetForm() {
    setName(""); setEmail(""); setPassword(""); setTitle(""); setLocation(""); setFormError("");
  }

  function resetBulk() {
    setPdfFiles([]); setCsvFile(null); setBulkResults(null);
  }

  function handleBulkPdf(e: React.FormEvent) {
    e.preventDefault();
    if (!pdfFiles.length) return;
    const fd = new FormData();
    pdfFiles.forEach((f) => fd.append("files", f));
    bulkUpload(fd, {
      onSuccess: (data) => {
        setBulkResults(data.results);
        toast.success(`${data.queued}/${data.total} resumes queued for processing.`);
      },
      onError: (err) => toast.error(err.message || "Bulk upload failed."),
    });
  }

  function handleCsvImport(e: React.FormEvent) {
    e.preventDefault();
    if (!csvFile) return;
    const fd = new FormData();
    fd.append("file", csvFile);
    csvImport(fd, {
      onSuccess: (data) => {
        setBulkResults(data.results);
        toast.success(`${data.queued}/${data.total} employees imported.`);
      },
      onError: (err) => toast.error(err.message || "CSV import failed."),
    });
  }

  function handleAddEmployee(e: React.FormEvent) {
    e.preventDefault();
    setFormError("");
    createEmployee(
      { name: name.trim(), email, password, title: title.trim() || undefined, location: location.trim() || undefined },
      {
        onSuccess: (emp) => {
          toast.success(`${emp.name} added — share login credentials with them.`);
          setOpen(false);
          resetForm();
        },
        onError: (err) => {
          setFormError(err instanceof ApiError ? err.message : "Failed to create employee.");
        },
      }
    );
  }

  return (
    <div className="px-4 sm:px-8 py-8 max-w-5xl mx-auto animate-fade-up">
      <div className="mb-8 pb-6 border-b border-[var(--color-border)] flex items-end justify-between gap-4">
        <div>
          <div className="w-8 h-0.5 bg-gradient-to-r from-emerald-500 to-teal-500 rounded-full mb-3" />
          <h1 className="text-2xl font-bold">Employee Directory</h1>
          <p className="text-sm text-[var(--color-muted-foreground)] mt-1">
            {employees ? `${employees.length} employees` : "Loading…"}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Bulk Import Dialog */}
          <Dialog.Root open={bulkOpen} onOpenChange={(v) => { setBulkOpen(v); if (!v) resetBulk(); }}>
            <Dialog.Trigger asChild>
              <button className="flex items-center gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] px-4 py-2.5 text-sm font-semibold text-[var(--color-foreground)] hover:bg-[var(--color-muted)] transition cursor-pointer shadow-sm">
                <Upload className="h-4 w-4" />
                Bulk Import
              </button>
            </Dialog.Trigger>

            <Dialog.Portal>
              <Dialog.Overlay className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm" />
              <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-lg -translate-x-1/2 -translate-y-1/2 rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-6 shadow-2xl">
                <div className="flex items-center justify-between mb-5">
                  <Dialog.Title className="text-base font-semibold">Bulk Import</Dialog.Title>
                  <Dialog.Close className="rounded-lg p-1.5 hover:bg-[var(--color-muted)] transition cursor-pointer">
                    <X className="h-4 w-4" />
                  </Dialog.Close>
                </div>

                {/* Tabs */}
                <div className="flex gap-1 rounded-lg bg-[var(--color-muted)] p-1 mb-5">
                  {(["pdf", "csv"] as BulkTab[]).map((t) => (
                    <button
                      key={t}
                      onClick={() => { setBulkTab(t); setBulkResults(null); }}
                      className={cn(
                        "flex-1 rounded-md py-1.5 text-sm font-medium transition-colors cursor-pointer",
                        bulkTab === t
                          ? "bg-[var(--color-card)] text-[var(--color-foreground)] shadow-sm"
                          : "text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]"
                      )}
                    >
                      {t === "pdf" ? "Multiple PDFs" : "CSV File"}
                    </button>
                  ))}
                </div>

                {bulkTab === "pdf" ? (
                  <form onSubmit={handleBulkPdf} className="space-y-4">
                    <div
                      onClick={() => pdfInputRef.current?.click()}
                      className="cursor-pointer rounded-xl border-2 border-dashed border-[var(--color-border)] p-8 text-center hover:border-indigo-400 hover:bg-indigo-50/30 transition"
                    >
                      <input
                        ref={pdfInputRef}
                        type="file"
                        accept=".pdf"
                        multiple
                        className="hidden"
                        onChange={(e) => setPdfFiles(Array.from(e.target.files ?? []))}
                      />
                      <Upload className="h-8 w-8 mx-auto text-[var(--color-muted-foreground)] mb-2" />
                      <p className="text-sm font-medium">Drop PDFs here or click to browse</p>
                      <p className="text-xs text-[var(--color-muted-foreground)] mt-1">Up to 20 PDFs · 10 MB each</p>
                    </div>
                    {pdfFiles.length > 0 && (
                      <div className="space-y-1 max-h-32 overflow-y-auto">
                        {pdfFiles.map((f, i) => (
                          <div key={i} className="flex items-center gap-2 text-xs text-[var(--color-muted-foreground)] rounded border border-[var(--color-border)] px-3 py-1.5">
                            <FileText className="h-3.5 w-3.5 shrink-0" />
                            <span className="truncate">{f.name}</span>
                            <span className="ml-auto shrink-0">{(f.size / 1024).toFixed(0)} KB</span>
                          </div>
                        ))}
                      </div>
                    )}
                    {bulkResults && <BulkResultsTable results={bulkResults} />}
                    <button
                      type="submit"
                      disabled={isBulkUploading || !pdfFiles.length}
                      className="w-full rounded-lg bg-gradient-to-r from-indigo-500 to-indigo-600 py-2.5 text-sm font-semibold text-white disabled:opacity-60 hover:from-indigo-600 hover:to-indigo-700 transition cursor-pointer"
                    >
                      {isBulkUploading ? "Uploading…" : `Upload ${pdfFiles.length || ""} PDF${pdfFiles.length !== 1 ? "s" : ""}`}
                    </button>
                  </form>
                ) : (
                  <form onSubmit={handleCsvImport} className="space-y-4">
                    <div
                      onClick={() => csvInputRef.current?.click()}
                      className="cursor-pointer rounded-xl border-2 border-dashed border-[var(--color-border)] p-8 text-center hover:border-emerald-400 hover:bg-emerald-50/30 transition"
                    >
                      <input
                        ref={csvInputRef}
                        type="file"
                        accept=".csv"
                        className="hidden"
                        onChange={(e) => setCsvFile(e.target.files?.[0] ?? null)}
                      />
                      <FileText className="h-8 w-8 mx-auto text-[var(--color-muted-foreground)] mb-2" />
                      {csvFile ? (
                        <p className="text-sm font-medium">{csvFile.name}</p>
                      ) : (
                        <>
                          <p className="text-sm font-medium">Drop CSV here or click to browse</p>
                          <p className="text-xs text-[var(--color-muted-foreground)] mt-1">UTF-8 CSV</p>
                        </>
                      )}
                    </div>
                    <div className="rounded-lg bg-[var(--color-muted)] p-3 text-xs text-[var(--color-muted-foreground)] space-y-1">
                      <p className="font-semibold text-[var(--color-foreground)]">Required CSV columns</p>
                      <p><span className="font-mono">name</span>, <span className="font-mono">email</span>, <span className="font-mono">password</span></p>
                      <p className="text-[var(--color-muted-foreground)]">Optional: <span className="font-mono">title</span>, <span className="font-mono">location</span></p>
                    </div>
                    {bulkResults && <BulkResultsTable results={bulkResults} />}
                    <button
                      type="submit"
                      disabled={isCsvImporting || !csvFile}
                      className="w-full rounded-lg bg-gradient-to-r from-emerald-500 to-emerald-600 py-2.5 text-sm font-semibold text-white disabled:opacity-60 hover:from-emerald-600 hover:to-emerald-700 transition cursor-pointer"
                    >
                      {isCsvImporting ? "Importing…" : "Import CSV"}
                    </button>
                  </form>
                )}
              </Dialog.Content>
            </Dialog.Portal>
          </Dialog.Root>

          {/* Add Employee Dialog */}
          <Dialog.Root open={open} onOpenChange={(v) => { setOpen(v); if (!v) resetForm(); }}>
            <Dialog.Trigger asChild>
              <button className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-indigo-500 to-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:from-indigo-600 hover:to-indigo-700 transition cursor-pointer shadow-sm">
                <UserPlus className="h-4 w-4" />
                Add Employee
              </button>
            </Dialog.Trigger>

          <Dialog.Portal>
            <Dialog.Overlay className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm" />
            <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-6 shadow-2xl">
              <div className="flex items-center justify-between mb-5">
                <Dialog.Title className="text-base font-semibold">Add New Employee</Dialog.Title>
                <Dialog.Close className="rounded-lg p-1.5 hover:bg-[var(--color-muted)] transition cursor-pointer">
                  <X className="h-4 w-4" />
                </Dialog.Close>
              </div>

              <form onSubmit={handleAddEmployee} className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="col-span-2">
                    <label className="block text-sm font-medium mb-1.5">Full name <span className="text-red-500">*</span></label>
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="Jane Smith"
                      required
                      className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
                    />
                  </div>
                  <div className="col-span-2">
                    <label className="block text-sm font-medium mb-1.5">Email <span className="text-red-500">*</span></label>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="jane@company.com"
                      required
                      className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
                    />
                  </div>
                  <div className="col-span-2">
                    <label className="block text-sm font-medium mb-1.5">Temporary password <span className="text-red-500">*</span></label>
                    <input
                      type="text"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Min. 6 characters"
                      required
                      minLength={6}
                      className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1.5">Job title</label>
                    <input
                      type="text"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      placeholder="e.g. Backend Engineer"
                      className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1.5">Location</label>
                    <input
                      type="text"
                      value={location}
                      onChange={(e) => setLocation(e.target.value)}
                      placeholder="e.g. Pune"
                      className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
                    />
                  </div>
                </div>

                {formError && (
                  <p className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
                    {formError}
                  </p>
                )}

                <p className="text-xs text-[var(--color-muted-foreground)]">
                  Share the email and password with the employee so they can log in and upload their resume.
                </p>

                <div className="flex gap-2 pt-1">
                  <Dialog.Close asChild>
                    <button
                      type="button"
                      className="flex-1 rounded-lg border border-[var(--color-border)] py-2 text-sm font-medium hover:bg-[var(--color-muted)] transition cursor-pointer"
                    >
                      Cancel
                    </button>
                  </Dialog.Close>
                  <button
                    type="submit"
                    disabled={isCreating}
                    className="flex-1 rounded-lg bg-gradient-to-r from-indigo-500 to-indigo-600 py-2 text-sm font-semibold text-white hover:from-indigo-600 hover:to-indigo-700 disabled:opacity-60 transition cursor-pointer"
                  >
                    {isCreating ? "Creating…" : "Create account"}
                  </button>
                </div>
              </form>
            </Dialog.Content>
          </Dialog.Portal>
        </Dialog.Root>
        </div>
      </div>

      {/* Search */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--color-muted-foreground)]" />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Filter by name, skill, or location…"
          className="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] pl-9 pr-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-indigo-500/25 focus:border-indigo-500 transition-all duration-150 shadow-sm"
        />
      </div>

      {isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {[...Array(6)].map((_, i) => <SkeletonCard key={i} />)}
        </div>
      )}

      {!isLoading && employees?.length === 0 && (
        <div className="rounded-xl border border-dashed border-[var(--color-border)] p-12 text-center">
          <p className="text-sm text-[var(--color-muted-foreground)]">No employees found.</p>
        </div>
      )}

      {employees && employees.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 animate-fade-up stagger-children">
          {employees.map((emp) => (
            <Link
              key={emp.id}
              href={`/employees/${emp.id}`}
              className="group rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-4 hover:shadow-lg hover:border-indigo-200 dark:hover:border-indigo-800 hover:-translate-y-0.5 transition-all duration-200 shadow-sm"
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="min-w-0">
                  <p className="text-sm font-semibold truncate">{emp.name}</p>
                  <div className="flex flex-wrap items-center gap-2 mt-0.5 text-xs text-[var(--color-muted-foreground)]">
                    {emp.title && (
                      <span className="flex items-center gap-1">
                        <Briefcase className="h-3 w-3" />{emp.title}
                      </span>
                    )}
                    {emp.location && (
                      <span className="flex items-center gap-1">
                        <MapPin className="h-3 w-3" />{emp.location}
                      </span>
                    )}
                  </div>
                </div>
                <span className={cn(
                  "shrink-0 rounded-full border px-2.5 py-1 text-[10px] font-semibold",
                  AVAILABILITY_STYLE[emp.availability] ?? AVAILABILITY_STYLE.allocated,
                )}>
                  {AVAILABILITY_LABEL[emp.availability] ?? "Allocated"}
                </span>
              </div>

              {emp.top_skills.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {emp.top_skills.slice(0, 5).map((s) => (
                    <span
                      key={s}
                      className="rounded-full bg-[var(--color-muted)] px-2 py-0.5 text-[10px] text-[var(--color-muted-foreground)]"
                    >
                      {s}
                    </span>
                  ))}
                  {emp.top_skills.length > 5 && (
                    <span className="rounded-full bg-[var(--color-muted)] px-2 py-0.5 text-[10px] text-[var(--color-muted-foreground)]">
                      +{emp.top_skills.length - 5}
                    </span>
                  )}
                </div>
              )}

              {emp.total_years_exp != null && (
                <p className="mt-2 text-xs text-[var(--color-muted-foreground)]">
                  {emp.total_years_exp}y experience
                </p>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
