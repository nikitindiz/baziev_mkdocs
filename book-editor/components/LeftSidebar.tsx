'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

interface LeftSidebarProps {
    children?: React.ReactNode;
}

const MIN_WIDTH = 300;
const MAX_WIDTH = 800;
const DEFAULT_WIDTH = 800;

export function LeftSidebar({ children }: LeftSidebarProps) {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [width, setWidth] = useState(DEFAULT_WIDTH);
    const [isResizing, setIsResizing] = useState(false);
    const sidebarRef = useRef<HTMLDivElement>(null);

    const isOpen = searchParams.get('show-symbols') === 'true';

    const toggleSidebar = () => {
        const params = new URLSearchParams(searchParams.toString());
        if (isOpen) {
            params.delete('show-symbols');
        } else {
            params.set('show-symbols', 'true');
        }
        router.push(`?${params.toString()}`, { scroll: false });
    };

    const handleMouseDown = (e: React.MouseEvent) => {
        e.preventDefault();
        setIsResizing(true);
    };

    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (!isResizing) return;

            const newWidth = e.clientX;
            if (newWidth >= MIN_WIDTH && newWidth <= MAX_WIDTH) {
                setWidth(newWidth);
            }
        };

        const handleMouseUp = () => {
            setIsResizing(false);
        };

        if (isResizing) {
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        }

        return () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        };
    }, [isResizing]);

    return (
        <>
            {/* Toggle Button (visible when sidebar is closed) */}
            {!isOpen && (
                <button
                    onClick={toggleSidebar}
                    className="fixed left-0 top-1/2 -translate-y-1/2 bg-blue-600 hover:bg-blue-700 text-white p-3 rounded-r-lg shadow-lg transition-all z-40"
                    aria-label="Открыть сайдбар символов"
                >
                    <svg fill="#FFF" version="1.1" id="Capa_1" xmlns="http://www.w3.org/2000/svg" xmlnsXlink="http://www.w3.org/1999/xlink"
                        width="800px" height="800px" viewBox="0 0 484.21 484.21"
                        xmlSpace="preserve"
                        style={{ maxWidth: 20, maxHeight: 20 }}>
                        <g>
                            <path d="M395.527,97.043V55.352H124.537l159.46,171.507c9.983,10.749,9.848,27.458-0.319,38.026L126.017,428.861h269.504v-25.18
		c0-15.256,12.413-27.668,27.674-27.668c15.256,0,27.681,12.412,27.681,27.668v52.848c0,15.262-12.419,27.681-27.681,27.681H61.014
		c-11.106,0-21.107-6.603-25.464-16.834c-4.359-10.226-2.189-22.012,5.509-30.026l184.584-191.964L40.743,46.521
		c-7.492-8.068-9.496-19.798-5.101-29.899C40.042,6.525,50.005,0,61.014,0h362.188c15.255,0,27.68,12.413,27.68,27.68v69.363
		c0,15.259-12.419,27.677-27.68,27.677C407.94,124.72,395.527,112.308,395.527,97.043z"/>
                        </g>
                    </svg>
                </button>
            )}

            {/* Sidebar */}
            <div
                ref={sidebarRef}
                className={`fixed left-0 top-0 h-full bg-white dark:bg-gray-800 shadow-2xl transition-transform duration-300 z-50 ${isOpen ? 'translate-x-0' : '-translate-x-full'
                    }`}
                style={{ width: `${width}px` }}
            >
                {/* Resize Handle */}
                <div
                    onMouseDown={handleMouseDown}
                    className="absolute right-0 top-0 w-1 h-full cursor-col-resize hover:bg-blue-500 transition-colors"
                    style={{
                        background: isResizing ? '#3b82f6' : 'transparent',
                    }}
                >
                    <div className="absolute right-0 top-1/2 -translate-y-1/2 w-1 h-20 bg-gray-300 dark:bg-gray-600 rounded-l" />
                </div>

                {/* Sidebar Content */}
                <div className="flex flex-col h-full pr-2">
                    {/* Header */}
                    <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
                        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                            Символы
                        </h2>
                        <button
                            onClick={toggleSidebar}
                            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                            aria-label="Закрыть сайдбар символов"
                        >
                            <svg
                                xmlns="http://www.w3.org/2000/svg"
                                className="h-6 w-6 text-gray-600 dark:text-gray-400"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M6 18L18 6M6 6l12 12"
                                />
                            </svg>
                        </button>
                    </div>

                    {/* Body */}
                    <div className="flex-1 overflow-y-auto">
                        {children}
                    </div>
                </div>
            </div>

            {/* Overlay (visible when sidebar is open) */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black/50 z-40 transition-opacity"
                    onClick={toggleSidebar}
                />
            )}
        </>
    );
}
