/**
 * @packageDocumentation This component is the home page of the application.
 */

import { Link } from "react-router-dom";
import {
    NewSubtitleIcon,
    UploadIcon,
    MicIcon,
    SaveIcon,
    NewGptIcon,
    GitHubIcon,
    ChevronRightIcon,
    StatsIcon,
} from "./Icons";
import { ScrollTextIcon } from "lucide-react";
/**
 * The HomePage component.
 *
 * This component is responsible for the following:
 * - Displaying the hero section.
 * - Displaying the features section.
 * - Displaying the footer.
 *
 * @returns {JSX.Element} The HomePage component.
 */
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
        <div className="min-h-screen select-none bg-gradient-to-br from-slate-900 to-gray-900 text-gray-100 font-sans antialiased">
            <header className="absolute top-0 left-0 p-4 space-x-4">
                <a
                    href="https://github.com/svdC1/mirumoji"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-colors"
                >
                    <GitHubIcon />
                    GitHub Repo
                </a>
                <a
                    href="https://svdc1.github.io/mirumoji/docs"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center space-x-2 px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-colors"
                >
                    <ScrollTextIcon size={20} />
                    <p>Docs</p>
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
                <footer className="flex flex-col items-center py-16 border-t border-slate-700/50">
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
