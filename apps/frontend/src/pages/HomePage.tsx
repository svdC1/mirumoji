import { Link } from "react-router-dom";
const GitHubIcon = () => (
    <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24">
        <path
            fillRule="evenodd"
            d="M12 2C6.477 2 2 6.477 2 12c0 4.418 2.865 8.165 6.839 9.489.5.092.682-.217.682-.482 0-.237-.009-.868-.014-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.031-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.82c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.378.203 2.397.1 2.65.64.7 1.03 1.595 1.03 2.688 0 3.848-2.338 4.695-4.566 4.942.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.577.688.482A10.001 10.001 0 0022 12c0-5.523-4.477-10-10-10z"
            clipRule="evenodd"
        />
    </svg>
);

const ChevronRightIcon = () => (
    <svg
        className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
    >
        <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M9 5l7 7-7 7"
        ></path>
    </svg>
);

const NewSubtitleIcon = () => (
    <svg
        className="w-10 h-10 mb-4 text-indigo-400"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
    >
        <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M4 6h16M4 10h16M4 14h10M18 14a2 2 0 11-4 0 2 2 0 014 0zM4 18h5"
        />
    </svg>
);
const NewGptIcon = () => (
    <svg
        className="w-10 h-10 mb-4 text-indigo-400"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
    >
        <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
        />
    </svg>
);
const UploadIcon = () => (
    <svg
        className="w-10 h-10 mb-4 text-indigo-400"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
    >
        <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
        />
    </svg>
);
const MicIcon = () => (
    <svg
        className="w-10 h-10 mb-4 text-indigo-400"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
    >
        <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
        />
    </svg>
);
const SaveIcon = () => (
    <svg
        className="w-10 h-10 mb-4 text-indigo-400"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
    >
        <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
        />
    </svg>
);
const StatsIcon = () => (
    <svg
        className="w-10 h-10 mb-4 text-indigo-400"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
    >
        <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
        />
    </svg>
);

export default function HomePage() {
    const featureList = [
        {
            icon: <NewSubtitleIcon />,
            title: "Interactive Subtitles",
            description:
                "Get dictionary entries for selected subtitles with a click and optionally display furigana.",
        },
        {
            icon: <NewGptIcon />,
            title: "GPT-Powered Nuance Explanation",
            description:
                "Get detailed breakdowns of grammar and nuances for any selected word or phrase, powered by GPT.",
        },
        {
            icon: <UploadIcon />,
            title: "Universal Video Uploads",
            description:
                "Upload videos in any format and convert them for smooth playback and subtitle sync.",
        },
        {
            icon: <MicIcon />,
            title: "Audio Transcription",
            description:
                "Transcribe your own Japanese audio recordings. Upload audio files and get accurate text to study with.",
        },
        {
            icon: <SaveIcon />,
            title: "Clip Saving & Management",
            description:
                "Save important video clips or specific subtitle segments for focused review and personalized study sessions.",
        },
        {
            icon: <StatsIcon />,
            title: "Export Clips to Anki",
            description:
                "Export saved clips with word meaning and GPT explanation as an Anki Deck.",
        },
    ];

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 to-gray-900 text-gray-100 font-sans antialiased">
            <header className="absolute top-0 left-0 p-4">
                <a
                    href="https://github.com/svdC1/mirumoji"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-colors"
                >
                    <GitHubIcon />
                    GitHub Repo
                </a>
            </header>
            <main className="pt-8">
                {/* Hero Section */}
                <section className="text-center py-20 md:py-32 px-6">
                    <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold mb-6 leading-tight text-white">
                        Immerse in Japanese with{" "}
                        <span className="text-indigo-400">Mirumoji</span>
                    </h1>
                    <p className="max-w-2xl mx-auto text-lg sm:text-xl md:text-2xl text-gray-300 mb-10">
                        Mirumoji uses AI to turn your favorite content into
                        immersive Japanese lessons.
                    </p>
                    <div className="flex flex-col sm:flex-row justify-center items-center gap-5">
                        <Link
                            to="/player"
                            className="group flex items-center justify-center px-8 py-3 bg-indigo-600 hover:bg-indigo-700 text-white text-lg rounded-lg font-bold transition duration-200 shadow-lg hover:shadow-xl transform hover:scale-105 w-full sm:w-auto"
                        >
                            Player <ChevronRightIcon />
                        </Link>
                        <Link
                            to="/transcribe"
                            className="group flex items-center justify-center px-8 py-3 border-2 border-indigo-500 text-indigo-400 hover:bg-indigo-500 hover:text-white text-lg rounded-lg font-bold transition duration-200 transform hover:scale-105 w-full sm:w-auto"
                        >
                            Transcribe Audio
                        </Link>
                    </div>
                </section>

                {/* Features Section - Enhanced Cards */}
                <section
                    id="features"
                    className="py-16 md:py-24 px-6 bg-slate-900/70 scroll-mt-20"
                >
                    <div className="max-w-7xl mx-auto">
                        <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-center mb-16 md:mb-20 text-white">
                            Immersion Toolkit
                        </h2>
                        <div className="grid sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 md:gap-10">
                            {featureList.map((feature) => (
                                <div
                                    key={feature.title}
                                    className="bg-gray-800/70 backdrop-blur-sm rounded-xl shadow-xl overflow-hidden flex flex-col transition-all duration-300 hover:shadow-indigo-500/40 hover:shadow-2xl hover:scale-[1.03]"
                                >
                                    <div className="p-6 md:p-8 text-center border-b-2 border-indigo-500/30">
                                        <div className="inline-block p-3 rounded-full bg-indigo-500/20 mb-4">
                                            {feature.icon}
                                        </div>
                                        <h3 className="text-xl md:text-2xl font-semibold mb-2 text-white">
                                            {feature.title}
                                        </h3>
                                    </div>
                                    <div className="p-6 md:p-8 flex-grow">
                                        <p className="text-gray-300 leading-relaxed text-sm md:text-base">
                                            {feature.description}
                                        </p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </section>

                {/* Footer */}
                <footer className="text-center py-16 border-t border-slate-700/50">
                    <p className="text-gray-500 text-sm">
                        © {new Date().getFullYear()} svdC1
                    </p>
                    <a
                        className="text-blue-500 text-sm"
                        href="https://github.com/svdC1/mirumoji/blob/main/LICENSE"
                    >
                        MIT LICENSE
                    </a>
                </footer>
            </main>
        </div>
    );
}
