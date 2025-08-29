# Progress Charts

A beautiful, minimalistic website showcasing human progress through interactive data visualizations.

## Features

- **Global Population Growth**: Interactive line chart showing population trends from 10,000 BCE to 2023
- **Population by Continent**: Stacked bar chart displaying continental population distribution over time
- **Life Expectancy**: Global life expectancy trends from 1950-2023
- **Fullscreen Charts**: Click the fullscreen button (⛶) to view charts in full screen
- **Responsive Design**: Optimized for all devices
- **Modern UI**: Clean, elegant design inspired by modern web aesthetics

## Tech Stack

- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Recharts** - Data visualization library
- **Framer Motion** - Animations
- **Tailwind CSS** - Utility-first CSS framework
- **SF Pro Display** - Typography

## Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/Prashan7h/Prashan7h.github.io.git
   cd Prashan7h.github.io/Progress
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Run development server**
   ```bash
   npm run dev
   ```

4. **Open your browser**
   Navigate to [http://localhost:3000](http://localhost:3000)

## Building for Production

```bash
npm run build
```

The static export will be generated in the `out/` folder.

## Deployment

This project is automatically deployed to GitHub Pages via GitHub Actions.

### Manual Deployment

1. **Build the project**
   ```bash
   npm run build
   ```

2. **Upload the `out/` folder contents** to your hosting provider
3. **Place in a folder called `progress`** for the `/progress` URL path

### GitHub Pages Setup

1. **Enable GitHub Pages** in your repository settings
2. **Set source to "GitHub Actions"**
3. **The workflow will automatically deploy** on every push to master

## Project Structure

```
Progress/
├── app/                    # Next.js app directory
│   ├── globals.css        # Global styles
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Main page component
├── components/             # React components
│   ├── PopulationChart.tsx           # Global population line chart
│   ├── ContinentalPopulationChart.tsx # Continental population bar chart
│   └── LifeExpectancyChart.tsx       # Life expectancy chart
├── .github/workflows/      # GitHub Actions
│   └── deploy.yml         # Deployment workflow
├── package.json           # Dependencies and scripts
├── next.config.js         # Next.js configuration
└── tsconfig.json          # TypeScript configuration
```

## Data Sources

- **Population Data**: Historical estimates from various sources (10,000 BCE - 2023)
- **Life Expectancy**: Global averages (1950-2023)
- **Continental Data**: Approximate population distribution by continent

## Customization

### Adding New Charts

1. Create a new component in `components/`
2. Import and add to `app/page.tsx`
3. Style with Tailwind CSS classes

### Modifying Data

Update the data arrays in each chart component:
- `PopulationChart.tsx` - `populationData`
- `ContinentalPopulationChart.tsx` - `continentalData`
- `LifeExpectancyChart.tsx` - `lifeExpectancyData`

### Styling

- **Global styles**: `app/globals.css`
- **Component styles**: Tailwind CSS classes
- **Custom CSS**: Add to `globals.css` or component files

## License

This project is open source and available under the [MIT License](LICENSE).

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For questions or issues, please open a GitHub issue or contact the maintainer.
