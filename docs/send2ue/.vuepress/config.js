const {description, repository, name} = require('../../package')

module.exports = {
    /**
     * Ref：https://v1.vuepress.vuejs.org/config/#title
     */
    title: 'Send to Unreal',
    base: process.env.PROD === '1' ? `/${name}/send2ue/` : '/',
    /**
     * Ref：https://v1.vuepress.vuejs.org/config/#description
     */
    description: description,

    /**
     * Extra tags to be injected to the page HTML `<head>`
     *
     * ref：https://v1.vuepress.vuejs.org/config/#head
     */
    head: [
        ['meta', {name: 'theme-color', content: '#3eaf7c'}],
        ['meta', {name: 'apple-mobile-web-app-capable', content: 'yes'}],
        ['meta', {name: 'apple-mobile-web-app-status-bar-style', content: 'black'}]
    ],

    /**
     * Theme configuration, here is the default theme configuration for VuePress.
     *
     * ref：https://v1.vuepress.vuejs.org/theme/default-theme-config.html
     */
    themeConfig: {
        repo: repository,
        docsDir: 'docs/send2ue',
        editLinks: true,
        editLinkText: 'Help us improve this page!',
        lastUpdated: false,
        nav: [
            {
                text: 'Home',
                link: process.env.PROD === '1' ? 'https://epicgames.github.io/BlenderTools/' : '/',
                target:'_self',
                rel:false
            }
        ],
        sidebar: {
            '/': [
                {
                    title: 'Introduction',
                    collapsable: false,
                    children: [
                        'introduction/quickstart'
                    ]
                },
                {
                    title: 'Asset Types',
                    collapsable: false,
                    children: [
                        'asset-types/skeletal-mesh',
                        'asset-types/static-mesh',
                        'asset-types/animation'
                    ]
                },
                {
                    title: 'Settings',
                    collapsable: false,
                    children: [
                        'settings/paths',
                        'settings/export',
                        'settings/import',
                        'settings/validations',
                    ]
                },
                {
                    title: 'Customize',
                    collapsable: false,
                    children: [
                        'customize/templates',
                        'customize/python-api',
                        'customize/extensions'
                    ]
                },
                {
                    title: 'Extras',
                    collapsable: false,
                    children: [
                        'extras/pipeline-menu',
                        'extras/addon-preferences',
                        'extras/supported-extensions',
                        'extras/community-extensions',
                    ]
                },
                {
                    title: 'Trouble Shooting',
                    collapsable: false,
                    children: [
                        'trouble-shooting/faq',
                        'trouble-shooting/errors',
                    ]
                }
            ],
        }
    },

    /**
     * Apply plugins，ref：https://v1.vuepress.vuejs.org/zh/plugin/
     */
    plugins: [
        '@vuepress/plugin-back-to-top',
        '@vuepress/plugin-medium-zoom',
    ]
}
