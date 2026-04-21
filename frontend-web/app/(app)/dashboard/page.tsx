import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Users, MessageSquare, TrendingUp, Car } from "lucide-react";

const STATS = [
  { label: "Активные клиенты", value: "—", icon: Users },
  { label: "Диалоги сегодня", value: "—", icon: MessageSquare },
  { label: "Автомобили", value: "—", icon: Car },
  { label: "Возвратность", value: "—", icon: TrendingUp },
];

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Обзор</h2>
        <p className="text-muted-foreground">Метрики вашего автосервиса</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {STATS.map(({ label, value, icon: Icon }) => (
          <Card key={label}>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
              <Icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{value}</div>
            </CardContent>
          </Card>
        ))}
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Добро пожаловать</CardTitle>
        </CardHeader>
        <CardContent className="text-muted-foreground">
          Команда ещё не настроена. Создайте команду в разделе Настройки, чтобы начать работу с клиентами.
        </CardContent>
      </Card>
    </div>
  );
}
