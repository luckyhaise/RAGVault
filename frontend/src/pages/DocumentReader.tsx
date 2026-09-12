import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";

import { fetchDocumentText } from "../api/documents";
import { DOCUMENT_TEXT_PAGE_SIZE } from "../config";
import { Alert } from "../components/StatusMessage";
import { Button } from "../components/ui/Button";
import { ChevronLeftIcon } from "../components/ui/Icons";
import type { DocumentSummary } from "../types/document_types";

interface DocumentReaderProps {
  document: DocumentSummary;
  onBack: () => void;
}

interface Chunk {
  start: number;
  text: string;
}

/**
 * How many character windows to keep mounted. Content beyond this is dropped
 * from the edge the reader is moving away from, which keeps memory bounded and
 * makes both the "next" and "previous" endpoints meaningful while scrolling.
 */
const MAX_CHUNKS = 16;

/** Sentinels sit slightly inside the viewport so loading starts before the edge. */
const PREFETCH_MARGIN_PX = "300px 0px";

export function DocumentReader({ document, onBack }: DocumentReaderProps) {
  const [chunks, setChunks] = useState<Chunk[]>([]);
  const [totalLength, setTotalLength] = useState(0);
  const [initialLoading, setInitialLoading] = useState(true);
  const [loadingPrevious, setLoadingPrevious] = useState(false);
  const [loadingNext, setLoadingNext] = useState(false);
  const [reachedStart, setReachedStart] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);
  const topSentinelRef = useRef<HTMLDivElement>(null);
  const bottomSentinelRef = useRef<HTMLDivElement>(null);
  // Prevents the two directions from firing at once.
  const busyRef = useRef(false);
  // A chunk element plus its viewport position, captured just before the loaded
  // text changes. Used to keep the reading position stable regardless of whether
  // content was added above, below, or trimmed.
  const anchorRef = useRef<{ key: number; top: number } | null>(null);
  const chunkElementsRef = useRef(new Map<number, HTMLSpanElement>());

  const loadedStart = chunks.length > 0 ? chunks[0].start : 0;
  const lastChunk = chunks.length > 0 ? chunks[chunks.length - 1] : null;
  const loadedEnd = lastChunk ? lastChunk.start + lastChunk.text.length : 0;
  const hasMorePrevious = loadedStart > 0 && !reachedStart;
  const hasMoreNext = totalLength > 0 && loadedEnd < totalLength;

  // Load the first window when the page opens. The request is aborted on cleanup
  // so React StrictMode's double-invoked effect (and a fast document switch) does
  // not fire two overlapping requests for the same first page.
  useEffect(() => {
    const controller = new AbortController();

    fetchDocumentText(
      {
        id: document.id,
        start: 0,
        limit: DOCUMENT_TEXT_PAGE_SIZE,
        prev: false,
      },
      controller.signal,
    )
      .then((result) => {
        const firstChunk = typeof result.items === "string" ? result.items : "";
        setChunks(firstChunk.length > 0 ? [{ start: 0, text: firstChunk }] : []);
        setTotalLength(result.pagination?.text_length ?? firstChunk.length);
        setError(null);
      })
      .catch((caught: unknown) => {
        if (controller.signal.aborted) return;
        setError(
          caught instanceof Error ? caught.message : "Unable to load document",
        );
      })
      .finally(() => {
        if (!controller.signal.aborted) setInitialLoading(false);
      });

    return () => controller.abort();
  }, [document.id]);

  // Remember where a surviving chunk sits before we change the loaded text.
  const rememberAnchor = useCallback(() => {
    const middle = chunks[Math.floor(chunks.length / 2)];
    if (!middle) return;
    const element = chunkElementsRef.current.get(middle.start);
    if (!element) return;
    anchorRef.current = {
      key: middle.start,
      top: element.getBoundingClientRect().top,
    };
  }, [chunks]);

  // After the DOM updates, shift the scroll position by however far the anchor
  // moved, which exactly cancels any layout shift above the viewport.
  useLayoutEffect(() => {
    const anchor = anchorRef.current;
    const container = scrollRef.current;
    anchorRef.current = null;
    if (!anchor || !container) return;

    const element = chunkElementsRef.current.get(anchor.key);
    if (!element) return;

    const delta = element.getBoundingClientRect().top - anchor.top;
    if (delta !== 0) container.scrollTop += delta;
  }, [chunks]);

  const loadNext = useCallback(async () => {
    if (busyRef.current || initialLoading) return;
    if (totalLength > 0 && loadedEnd >= totalLength) return;

    busyRef.current = true;
    setLoadingNext(true);
    rememberAnchor();
    const start = loadedEnd;
    try {
      const result = await fetchDocumentText({
        id: document.id,
        start,
        limit: DOCUMENT_TEXT_PAGE_SIZE,
        prev: false,
      });
      const chunkText = typeof result.items === "string" ? result.items : "";

      if (chunkText.length === 0) {
        // Server has no more text: stop the sentinel from re-triggering.
        setTotalLength(start);
        return;
      }

      setTotalLength((current) => result.pagination?.text_length ?? current);
      setChunks((current) => {
        const appended = [...current, { start, text: chunkText }];
        return appended.length > MAX_CHUNKS
          ? appended.slice(appended.length - MAX_CHUNKS)
          : appended;
      });
      setError(null);
    } catch (caught) {
      anchorRef.current = null;
      setError(
        caught instanceof Error ? caught.message : "Unable to load more",
      );
    } finally {
      setLoadingNext(false);
      busyRef.current = false;
    }
  }, [document.id, initialLoading, loadedEnd, rememberAnchor, totalLength]);

  const loadPrevious = useCallback(async () => {
    if (busyRef.current || initialLoading) return;
    if (!hasMorePrevious) return;

    busyRef.current = true;
    setLoadingPrevious(true);
    rememberAnchor();
    const start = loadedStart;
    try {
      const result = await fetchDocumentText({
        id: document.id,
        start,
        limit: DOCUMENT_TEXT_PAGE_SIZE,
        prev: true,
      });
      const chunkText = typeof result.items === "string" ? result.items : "";

      if (chunkText.length === 0) {
        anchorRef.current = null;
        setReachedStart(true);
        return;
      }

      setTotalLength((current) => result.pagination?.text_length ?? current);
      setChunks((current) => {
        const prepended = [
          { start: Math.max(0, start - chunkText.length), text: chunkText },
          ...current,
        ];
        return prepended.length > MAX_CHUNKS
          ? prepended.slice(0, MAX_CHUNKS)
          : prepended;
      });
      setError(null);
    } catch (caught) {
      anchorRef.current = null;
      setError(
        caught instanceof Error ? caught.message : "Unable to load earlier text",
      );
    } finally {
      setLoadingPrevious(false);
      busyRef.current = false;
    }
  }, [document.id, hasMorePrevious, initialLoading, loadedStart, rememberAnchor]);

  // Keep the newest loaders reachable from the observer without making the
  // observer depend on them. If the observer depended on `loadNext`/`loadPrevious`
  // it would be torn down and rebuilt after every loaded page, and a freshly
  // created IntersectionObserver immediately re-reports the sentinels that are
  // already on screen. That re-report fired another load with no scroll, which
  // chained page after page until the next page was large enough to push the
  // sentinel off-screen — effectively downloading the whole document at once.
  const loadNextRef = useRef(loadNext);
  const loadPreviousRef = useRef(loadPrevious);
  useEffect(() => {
    loadNextRef.current = loadNext;
    loadPreviousRef.current = loadPrevious;
  }, [loadNext, loadPrevious]);

  // Scroll-driven loading: watch sentinels at both ends of the text. Subscribed
  // once per document, so a load only ever follows an actual scroll into view.
  useEffect(() => {
    const container = scrollRef.current;
    const topSentinel = topSentinelRef.current;
    const bottomSentinel = bottomSentinelRef.current;
    if (!container || !topSentinel || !bottomSentinel) return;

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue;
          if (entry.target === topSentinel) {
            void loadPreviousRef.current();
          } else if (entry.target === bottomSentinel) {
            void loadNextRef.current();
          }
        }
      },
      { root: container, rootMargin: PREFETCH_MARGIN_PX },
    );

    observer.observe(topSentinel);
    observer.observe(bottomSentinel);
    return () => observer.disconnect();
  }, [document.id]);

  // If a single page does not fill the scroll container, top it up until it does
  // (or the document ends). Unlike the old observer re-subscription this cannot
  // run away: it stops as soon as the content overflows the visible area, so at
  // most one viewport's worth of text is ever requested without a scroll.
  useEffect(() => {
    if (initialLoading || loadingNext || loadingPrevious) return;
    if (!hasMoreNext) return;
    const container = scrollRef.current;
    if (!container) return;
    if (container.scrollHeight > container.clientHeight + 1) return;
    void loadNext();
  }, [
    initialLoading,
    loadingNext,
    loadingPrevious,
    hasMoreNext,
    loadNext,
    chunks,
    totalLength,
  ]);

  const title = document.title?.trim() || "Untitled document";

  return (
    <div className="flex h-screen flex-col bg-slate-100">
      <header className="z-30 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-3xl items-center gap-4 px-4 py-3 sm:px-6">
          <Button variant="ghost" size="sm" onClick={onBack}>
            <ChevronLeftIcon />
            Back
          </Button>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold text-slate-900">{title}</p>
            <p className="text-xs text-slate-500">
              {totalLength > 0
                ? `${totalLength.toLocaleString()} characters`
                : "Loading…"}
            </p>
          </div>
        </div>
      </header>

      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6">
          {/* Both sentinels stay mounted for the whole session so the observer
              can attach once, before any text has arrived. */}
          <div ref={topSentinelRef} aria-hidden="true" className="h-px" />

          {error && (
            <div className="mb-4">
              <Alert type="error" message={error} />
            </div>
          )}

          {initialLoading ? (
            <div className="flex h-64 items-center justify-center text-sm text-slate-500">
              Loading document…
            </div>
          ) : chunks.length === 0 ? (
            <div className="flex h-64 items-center justify-center text-sm text-slate-400">
              This document has no text content.
            </div>
          ) : (
            <>
              {loadingPrevious && (
                <p className="py-4 text-center text-xs text-slate-400">
                  Loading earlier text…
                </p>
              )}

              <pre className="whitespace-pre-wrap break-words font-mono text-[13px] leading-relaxed text-slate-800">
                {chunks.map((chunk) => (
                  <span
                    key={chunk.start}
                    ref={(element) => {
                      if (element) {
                        chunkElementsRef.current.set(chunk.start, element);
                      } else {
                        chunkElementsRef.current.delete(chunk.start);
                      }
                    }}
                  >
                    {chunk.text}
                  </span>
                ))}
              </pre>

              {loadingNext && (
                <p className="py-4 text-center text-xs text-slate-400">
                  Loading more…
                </p>
              )}
              {!hasMoreNext && (
                <p className="py-8 text-center text-[10px] uppercase tracking-widest text-slate-400">
                  End of document
                </p>
              )}
            </>
          )}

          <div ref={bottomSentinelRef} aria-hidden="true" className="h-px" />
        </div>
      </div>
    </div>
  );
}
