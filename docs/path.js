const {name} = require('./package')

export const getRootPath = (addon_name='') => {
    if (process.env.PROD === '1') {
        if (addon_name !== '')
        {
            return `/${name}/${addon_name}/`
        } else {
            return `/${name}/`
        }
    }
    if (process.env.TEST === '1') {
        if (addon_name !== '')
        {
            return `/${addon_name}/`
        } else {
            return '/'
        }
    }
    return  '/'
}
