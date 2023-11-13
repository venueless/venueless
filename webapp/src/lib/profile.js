import i18n from 'i18n'

export function getUserName (user) {
	if (user.deleted) return i18n.t('User:label:deleted')
	return user.profile?.display_name ?? user.sender ?? '(unknown user)'
}
