export function LoadingScreen({ message }: { message?: string }) {
  return (
    <div className="h-screen flex flex-col items-center justify-center gap-3 bg-background">
      <i className="fa-solid fa-spinner fa-spin text-3xl text-primary"></i>
      {message && <p className="text-sm text-muted-foreground">{message}</p>}
    </div>
  )
}