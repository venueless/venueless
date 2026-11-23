import i18n from 'i18n'

export default function errorMessage (error) {
	switch (error?.apiError?.code) {
		case 'auth.denied':
		case 'protocol.denied':
			return i18n.t('error:denied')
		case 'user.not_found':
		case 'room.unknown':
		case 'poster.unknown_poster':
		case 'exhibition.unknown_exhibitor':
			return i18n.t('error:not-found')
		case 'user.delete.self':
		case 'user.ban.self':
		case 'user.silence.self':
		case 'user.reactivate.self':
		case 'user.block.self':
			return i18n.t('error:self')
		default:
			return i18n.t('error:unknown')
	}
}
