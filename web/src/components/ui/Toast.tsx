import { useUiStore } from '../../store/uiStore';

export const Toast = () => {
  const { toastMessage, setToastMessage } = useUiStore();
  if (!toastMessage) return null;

  return (
    <button
      className="fixed bottom-4 right-4 rounded-md bg-brand-700 px-4 py-2 text-sm font-semibold text-white"
      onClick={() => setToastMessage(null)}
      type="button"
    >
      {toastMessage}
    </button>
  );
};
