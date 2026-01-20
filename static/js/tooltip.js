/**
 * Global Tooltip Handler
 * Dynamically positions tooltips centered over elements within the viewport
 */
document.addEventListener('DOMContentLoaded', () => {
    // Create tooltip element if it doesn't exist
    let tooltip = document.getElementById('globalTooltip');
    if (!tooltip) {
        tooltip = document.createElement('div');
        tooltip.id = 'globalTooltip';
        tooltip.className = 'custom-tooltip';
        document.body.appendChild(tooltip);
    }

    let activeTarget = null;

    const updatePosition = (targetRect) => {
        const padding = 20;
        const tooltipRect = tooltip.getBoundingClientRect();

        // Horizontal centering
        let x = targetRect.left + (targetRect.width / 2) - (tooltipRect.width / 2);

        // Vertical positioning (default above)
        let y = targetRect.top - tooltipRect.height - 12;

        // Viewport boundaries check - Horizontal
        if (x < padding) {
            x = padding;
        } else if (x + tooltipRect.width > window.innerWidth - padding) {
            x = window.innerWidth - tooltipRect.width - padding;
        }

        // Viewport boundaries check - Vertical
        // If no space above, flip to bottom
        if (y < padding) {
            y = targetRect.bottom + 12;

            // If still no space at bottom, just keep it within viewport
            if (y + tooltipRect.height > window.innerHeight - padding) {
                y = window.innerHeight - tooltipRect.height - padding;
            }
        }

        tooltip.style.left = `${x}px`;
        tooltip.style.top = `${y}px`;
    };

    const handleMouseOver = (e) => {
        const target = e.target.closest('[data-tooltip]');

        if (target) {
            if (activeTarget === target) return;

            const content = target.getAttribute('data-tooltip');
            if (content) {
                tooltip.textContent = content;
                tooltip.classList.add('active');
                activeTarget = target;

                // Use requestAnimationFrame to ensure tooltip is rendered and has size
                requestAnimationFrame(() => {
                    const rect = target.getBoundingClientRect();
                    updatePosition(rect);
                });
            }
        } else {
            tooltip.classList.remove('active');
            activeTarget = null;
        }
    };

    // Use event delegation for performance and handling dynamic elements
    document.addEventListener('mouseover', handleMouseOver);

    // Hide tooltip when window is scrolled or resized
    window.addEventListener('scroll', () => {
        tooltip.classList.remove('active');
        activeTarget = null;
    }, { passive: true });

    window.addEventListener('resize', () => {
        tooltip.classList.remove('active');
        activeTarget = null;
    }, { passive: true });
});
