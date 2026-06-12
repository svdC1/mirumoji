/**
 * @packageDocumentation The 404 page.
 */

import { Link } from "react-router-dom";
import { buttonClasses, Card } from "@/shared/ui";

/**
 * The NotFoundPage component — a 404 message with a link home.
 *
 * @returns {JSX.Element} The NotFoundPage component.
 */
export default function NotFoundPage() {
    return (
        <div className="flex h-full flex-col items-center justify-center px-6 py-12 text-center">
            <Card className="w-full max-w-md p-8 md:p-12">
                <p className="font-display text-7xl font-semibold text-shu md:text-8xl">404</p>
                <h1 className="mt-4 font-display text-2xl text-ink md:text-3xl">Page Not Found</h1>
                <p className="mb-8 mt-3 text-sm text-ink-muted md:text-base">
                    The Page You&apos;re Looking For Doesn&apos;t Exist
                </p>
                <Link to="/" className={buttonClasses("primary", "lg")}>
                    Go To Home
                </Link>
            </Card>
        </div>
    );
}
