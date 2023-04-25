const {description, repository} = require('../../package')
const { getRootPath } = require('../../path')
import { defaultTheme } from '@vuepress/theme-default'
import { defineUserConfig } from '@vuepress/cli'
import { palettePlugin } from '@vuepress/plugin-palette'
// @ts-ignore
import { googleAnalyticsPlugin } from '@vuepress/plugin-google-analytics'


export default defineUserConfig({
    title: 'Send to Unreal',
    description: description,
    base: getRootPath('send2ue'),
    theme: defaultTheme({
        repo: repository,
        docsDir: 'docs/send2ue',
        editLinkText: 'Help us improve this page!',
        lastUpdated: false,

        navbar: [
            {
                text: 'Home',
                link: process.env.PROD === '1' ? 'https://epicgames.github.io/BlenderTools/' : '/',
                target:'_self'
            }
        ],
        sidebar: {
            '/': [
                {
                    text: 'Introduction',
                    children: [
                        '/introduction/quickstart'
                    ]
                },
                {
                    text: 'Asset Types',
                    children: [
                        '/asset-types/skeletal-mesh',
                        '/asset-types/static-mesh',
                        '/asset-types/animation-sequence',
                        '/asset-types/groom'
                    ]
                },
                {
                    text: 'Settings',
                    children: [
                        '/settings/paths',
                        '/settings/export',
                        '/settings/import',
                        '/settings/validations',
                    ]
                },
                {
                    text: 'Customize',
                    children: [
                        '/customize/templates',
                        '/customize/python-api',
                        '/customize/extensions'
                    ]
                },
                {
                    text: 'Supported Extensions',
                    children: [
                        '/extensions/affixes',
                        '/extensions/combine-assets',
                        '/extensions/create-post-import-groom-assets',
                        '/extensions/ue2rigify',
                        '/extensions/use-immediate-parent-name',
                        '/extensions/use-collections-as-folders',
                        '/extensions/instance-assets'
                    ]
                },
                {
                    text: 'Extras',
                    children: [
                        '/extras/pipeline-menu',
                        '/extras/addon-preferences',
                        '/extras/community-extensions',
                    ]
                },
                {
                    text: 'Trouble Shooting',
                    children: [
                        '/trouble-shooting/faq',
                        '/trouble-shooting/errors',
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

