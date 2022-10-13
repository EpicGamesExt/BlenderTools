const {description, repository} = require('../../package')
const { getRootPath } = require('../../path')
import { defaultTheme } from '@vuepress/theme-default'
import { defineUserConfig } from '@vuepress/cli'
import { palettePlugin } from '@vuepress/plugin-palette'
// @ts-ignore
import { googleAnalyticsPlugin } from '@vuepress/plugin-google-analytics'


export default defineUserConfig({
    title: 'Documentation',
    description: description,
    base: getRootPath(),
    theme: defaultTheme({
        repo: repository,
        docsDir: 'docs/main',
        editLinkText: 'Help us improve this page!',
        lastUpdated: false,

        navbar: [
            {
                text: 'Home',
                link: '/',
            }
        ],
        sidebar: {
            '/': [
                {
                    text: 'Blender',
                    children: [
                        '/'
                    ]
                },
                {
                    text: 'Contributing',
                    children: [
                        '/contributing/development',
                        '/contributing/documentation',
                        '/contributing/testing',
                    ]
                }
            ],
        }
    }),

    plugins: [
        palettePlugin({preset: 'sass'}),
        googleAnalyticsPlugin({id: process.env.GA_ID})
    ]
})
