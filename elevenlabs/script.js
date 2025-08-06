// Slide navigation functionality
let currentSlide = 1;
const totalSlides = 13;

// Initialize the presentation
document.addEventListener('DOMContentLoaded', function() {
    // Set up navigation dots
    const dots = document.querySelectorAll('.dot');
    dots.forEach((dot, index) => {
        dot.addEventListener('click', () => {
            goToSlide(index + 1);
        });
    });

    // Set up navigation arrows
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('nav-arrow')) {
            if (e.target.classList.contains('next')) {
                nextSlide();
            } else if (e.target.classList.contains('prev')) {
                prevSlide();
            }
        }
    });

    // Set up main arrow on first slide
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('arrow')) {
            nextSlide();
        }
    });

    // Set up keyboard navigation
    document.addEventListener('keydown', function(e) {
        switch(e.key) {
            case 'ArrowRight':
            case ' ':
                nextSlide();
                break;
            case 'ArrowLeft':
                prevSlide();
                break;
            case 'Home':
                goToSlide(1);
                break;
            case 'End':
                goToSlide(totalSlides);
                break;
        }
    });

    // Set up touch/swipe navigation for mobile
    let touchStartX = 0;
    let touchStartY = 0;
    let touchEndX = 0;
    let touchEndY = 0;
    let isScrolling = false;

    document.addEventListener('touchstart', e => {
        touchStartX = e.changedTouches[0].screenX;
        touchStartY = e.changedTouches[0].screenY;
        isScrolling = false;
    }, { passive: true });

    document.addEventListener('touchmove', e => {
        const touchY = e.changedTouches[0].screenY;
        const touchX = e.changedTouches[0].screenX;
        
        // Check if user is scrolling vertically
        if (Math.abs(touchY - touchStartY) > Math.abs(touchX - touchStartX)) {
            isScrolling = true;
        }
    }, { passive: true });

    document.addEventListener('touchend', e => {
        if (isScrolling) return; // Don't handle swipe if user was scrolling
        
        touchEndX = e.changedTouches[0].screenX;
        touchEndY = e.changedTouches[0].screenY;
        handleSwipe();
    }, { passive: true });

    function handleSwipe() {
        const swipeThreshold = 50;
        const diffX = touchStartX - touchEndX;
        const diffY = Math.abs(touchStartY - touchEndY);
        
        // Only handle horizontal swipes, ignore vertical swipes
        if (Math.abs(diffX) > swipeThreshold && diffY < 100) {
            if (diffX > 0) {
                nextSlide();
            } else {
                prevSlide();
            }
        }
    }

    // Prevent zoom on double tap
    let lastTouchEnd = 0;
    document.addEventListener('touchend', function (event) {
        const now = (new Date()).getTime();
        if (now - lastTouchEnd <= 300) {
            event.preventDefault();
        }
        lastTouchEnd = now;
    }, false);
});

// Navigation functions
function nextSlide() {
    if (currentSlide < totalSlides) {
        goToSlide(currentSlide + 1);
    }
}

function prevSlide() {
    if (currentSlide > 1) {
        goToSlide(currentSlide - 1);
    }
}

function goToSlide(slideNumber) {
    // Validate slide number
    if (slideNumber < 1 || slideNumber > totalSlides) {
        return;
    }

    // Hide current slide
    const currentSlideElement = document.getElementById(`slide-${currentSlide}`);
    if (currentSlideElement) {
        currentSlideElement.classList.remove('active');
    }

    // Update current slide
    currentSlide = slideNumber;

    // Show new slide
    const newSlideElement = document.getElementById(`slide-${currentSlide}`);
    if (newSlideElement) {
        newSlideElement.classList.add('active');
    }

    // Update navigation dots
    updateNavigationDots();
}

function updateNavigationDots() {
    const dots = document.querySelectorAll('.dot');
    dots.forEach((dot, index) => {
        if (index + 1 === currentSlide) {
            dot.classList.add('active');
        } else {
            dot.classList.remove('active');
        }
    });
}

// Utility function to update content dynamically
function updateSlideContent(slideNumber, content) {
    const slide = document.getElementById(`slide-${slideNumber}`);
    if (slide) {
        // Update specific content based on the content object
        if (content.title) {
            const title = slide.querySelector('h2');
            if (title) title.textContent = content.title;
        }
        
        if (content.text) {
            const textContent = slide.querySelector('.text-content p');
            if (textContent) textContent.textContent = content.text;
        }
        
        if (content.originalText) {
            const originalText = slide.querySelector('.comparison-item:first-child .text-box p');
            if (originalText) originalText.textContent = content.originalText;
        }
        
        if (content.translatedText) {
            const translatedText = slide.querySelector('.comparison-item:last-child .text-box p');
            if (translatedText) translatedText.textContent = content.translatedText;
        }
        
        if (content.score) {
            const scoreElement = slide.querySelector('.score-value');
            if (scoreElement) scoreElement.textContent = content.score;
        }
    }
}

// Function to add new slides dynamically
function addSlide(slideNumber, slideHTML) {
    const presentationContainer = document.querySelector('.presentation-container');
    
    // Create new slide element
    const newSlide = document.createElement('section');
    newSlide.className = 'slide';
    newSlide.id = `slide-${slideNumber}`;
    newSlide.innerHTML = slideHTML;
    
    // Insert before the last slide (before the closing div)
    const lastSlide = presentationContainer.lastElementChild;
    presentationContainer.insertBefore(newSlide, lastSlide);
    
    // Add new navigation dot
    const navDots = document.querySelector('.nav-dots');
    const newDot = document.createElement('div');
    newDot.className = 'dot';
    newDot.setAttribute('data-slide', slideNumber);
    newDot.addEventListener('click', () => goToSlide(slideNumber));
    navDots.appendChild(newDot);
    
    // Update total slides count
    totalSlides = Math.max(totalSlides, slideNumber);
}

// Export functions for external use
window.presentationControls = {
    nextSlide,
    prevSlide,
    goToSlide,
    updateSlideContent,
    addSlide
}; 