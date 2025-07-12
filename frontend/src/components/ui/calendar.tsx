import * as React from "react"
import { cn } from "@/lib/utils"

export interface CalendarProps {
  selected?: Date
  onSelect?: (date: Date | undefined) => void
  className?: string
}

const Calendar = React.forwardRef<HTMLDivElement, CalendarProps>(
  ({ selected, onSelect, className, ...props }, ref) => {
    const today = new Date()
    const currentMonth = selected || today
    const year = currentMonth.getFullYear()
    const month = currentMonth.getMonth()

    const firstDayOfMonth = new Date(year, month, 1)
    const lastDayOfMonth = new Date(year, month + 1, 0)
    const firstDayOfWeek = firstDayOfMonth.getDay()
    const daysInMonth = lastDayOfMonth.getDate()

    const days = []
    
    // Empty cells for days before the first day of the month
    for (let i = 0; i < firstDayOfWeek; i++) {
      days.push(null)
    }
    
    // Days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      days.push(new Date(year, month, day))
    }

    const handlePrevMonth = () => {
      const prevMonth = new Date(year, month - 1, 1)
      onSelect?.(prevMonth)
    }

    const handleNextMonth = () => {
      const nextMonth = new Date(year, month + 1, 1)
      onSelect?.(nextMonth)
    }

    const handleDayClick = (date: Date) => {
      onSelect?.(date)
    }

    const monthNames = [
      "1月", "2月", "3月", "4月", "5月", "6月",
      "7月", "8月", "9月", "10月", "11月", "12月"
    ]

    const dayNames = ["日", "月", "火", "水", "木", "金", "土"]

    return (
      <div
        ref={ref}
        className={cn("p-4 bg-white border rounded-lg shadow-sm w-80", className)}
        {...props}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <button
            onClick={handlePrevMonth}
            className="p-1 hover:bg-gray-100 rounded"
          >
            ←
          </button>
          <div className="font-semibold">
            {year}年 {monthNames[month]}
          </div>
          <button
            onClick={handleNextMonth}
            className="p-1 hover:bg-gray-100 rounded"
          >
            →
          </button>
        </div>

        {/* Day names */}
        <div className="grid grid-cols-7 gap-1 mb-2">
          {dayNames.map((dayName) => (
            <div
              key={dayName}
              className="h-10 flex items-center justify-center text-sm font-medium text-gray-500"
            >
              {dayName}
            </div>
          ))}
        </div>

        {/* Calendar grid */}
        <div className="grid grid-cols-7 gap-1">
          {days.map((date, index) => (
            <div
              key={index}
              className="h-10 flex items-center justify-center"
            >
              {date && (
                <button
                  onClick={() => handleDayClick(date)}
                  className={cn(
                    "w-10 h-10 text-sm rounded hover:bg-gray-100",
                    selected &&
                      date.toDateString() === selected.toDateString() &&
                      "bg-blue-500 text-white hover:bg-blue-600",
                    date.toDateString() === today.toDateString() &&
                      "font-bold"
                  )}
                >
                  {date.getDate()}
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
    )
  }
)

Calendar.displayName = "Calendar"

export { Calendar }